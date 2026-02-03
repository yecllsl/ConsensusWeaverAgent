import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import yaml


class OS(Enum):
    WINDOWS = "Windows"
    MACOS = "Darwin"
    LINUX = "Linux"


class GPUVendor(Enum):
    NVIDIA = "NVIDIA"
    AMD = "AMD"
    INTEL = "Intel"
    APPLE = "Apple"
    UNKNOWN = "Unknown"


@dataclass
class CPUInfo:
    model: str
    cores: int
    threads: int
    frequency_ghz: float
    architecture: str
    features: List[str]


@dataclass
class GPUInfo:
    vendor: GPUVendor
    model: str
    vram_gb: float
    compute_capability: Optional[str] = None
    is_dedicated: bool = True


@dataclass
class MemoryInfo:
    total_gb: float
    available_gb: float
    type: str
    speed_mhz: Optional[float] = None


@dataclass
class HardwareInfo:
    os: OS
    cpu: CPUInfo
    gpu: Optional[GPUInfo]
    memory: MemoryInfo


@dataclass
class LlamaCppConfig:
    n_threads: int
    n_batch: int
    n_ctx: int
    n_gpu_layers: int
    quantization: str
    use_mmap: bool
    use_mlock: bool
    low_vram: bool
    split_mode: Optional[str] = None


@dataclass
class ConfigRecommendation:
    config: LlamaCppConfig
    reasoning: List[str]
    performance_expectation: str
    command_template: str


@dataclass
class ConfigValidation:
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]


class HardwareDetector:
    def __init__(self):
        self.os = self._detect_os()
        print(f"检测到操作系统: {self.os.value}")
        print("-" * 80)

    def _detect_os(self) -> OS:
        system = platform.system()
        if system == "Windows":
            return OS.WINDOWS
        elif system == "Darwin":
            return OS.MACOS
        elif system == "Linux":
            return OS.LINUX
        else:
            raise ValueError(f"不支持的操作系统: {system}")

    def detect_cpu(self) -> CPUInfo:
        print("正在检测CPU信息...")
        try:
            if self.os == OS.WINDOWS:
                return self._detect_cpu_windows()
            elif self.os == OS.LINUX:
                return self._detect_cpu_linux()
            elif self.os == OS.MACOS:
                return self._detect_cpu_macos()
        except Exception as e:
            print(f"CPU检测失败: {e}")
            return CPUInfo(
                model="Unknown",
                cores=4,
                threads=4,
                frequency_ghz=2.0,
                architecture="x86_64",
                features=[],
            )

    def _detect_cpu_windows(self) -> CPUInfo:
        import wmi

        c = wmi.WMI()
        cpu_info = c.Win32_Processor()[0]

        model = cpu_info.Name
        model = model.replace("(R)", "").replace("(TM)", "").strip()
        cores = cpu_info.NumberOfCores
        threads = cpu_info.NumberOfLogicalProcessors
        frequency_ghz = cpu_info.MaxClockSpeed / 1000.0

        features = []
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "Capabilities", "/value"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                capabilities = result.stdout
                if "AVX" in capabilities:
                    features.append("AVX")
                if "AVX2" in capabilities:
                    features.append("AVX2")
                if "AVX512" in capabilities:
                    features.append("AVX512")
        except Exception:
            pass

        architecture = platform.machine()

        print(f"  CPU型号: {model}")
        print(f"  物理核心: {cores}")
        print(f"  逻辑线程: {threads}")
        print(f"  主频: {frequency_ghz:.2f} GHz")
        print(f"  架构: {architecture}")
        if features:
            print(f"  特性: {', '.join(features)}")

        return CPUInfo(
            model=model,
            cores=cores,
            threads=threads,
            frequency_ghz=frequency_ghz,
            architecture=architecture,
            features=features,
        )

    def _detect_cpu_linux(self) -> CPUInfo:
        model = "Unknown"
        cores = 0
        threads = 0
        frequency_ghz = 0.0
        features = []

        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()

            model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo)
            if model_match:
                model = model_match.group(1).strip()

            cores = len(re.findall(r"processor\s*:", cpuinfo))
            threads = cores

            freq_match = re.search(r"cpu MHz\s*:\s*([\d.]+)", cpuinfo)
            if freq_match:
                frequency_ghz = float(freq_match.group(1)) / 1000.0

            flags_match = re.search(r"flags\s*:\s*(.+)", cpuinfo)
            if flags_match:
                flags = flags_match.group(1)
                if "avx" in flags:
                    features.append("AVX")
                if "avx2" in flags:
                    features.append("AVX2")
                if "avx512f" in flags:
                    features.append("AVX512")

        except Exception as e:
            print(f"  读取/proc/cpuinfo失败: {e}")

        architecture = platform.machine()

        print(f"  CPU型号: {model}")
        print(f"  逻辑线程: {threads}")
        print(f"  主频: {frequency_ghz:.2f} GHz")
        print(f"  架构: {architecture}")
        if features:
            print(f"  特性: {', '.join(features)}")

        return CPUInfo(
            model=model,
            cores=cores,
            threads=threads,
            frequency_ghz=frequency_ghz,
            architecture=architecture,
            features=features,
        )

    def _detect_cpu_macos(self) -> CPUInfo:
        model = "Unknown"
        cores = 0
        threads = 0
        frequency_ghz = 0.0
        features = []

        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                model = result.stdout.strip()

            result = subprocess.run(
                ["sysctl", "-n", "hw.physicalcpu"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                cores = int(result.stdout.strip())

            result = subprocess.run(
                ["sysctl", "-n", "hw.logicalcpu"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                threads = int(result.stdout.strip())

            result = subprocess.run(
                ["sysctl", "-n", "hw.cpufrequency"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                frequency_ghz = float(result.stdout.strip()) / 1_000_000_000.0

            features.append("NEON")

        except Exception as e:
            print(f"  macOS CPU检测失败: {e}")

        architecture = platform.machine()

        print(f"  CPU型号: {model}")
        print(f"  物理核心: {cores}")
        print(f"  逻辑线程: {threads}")
        print(f"  主频: {frequency_ghz:.2f} GHz")
        print(f"  架构: {architecture}")
        if features:
            print(f"  特性: {', '.join(features)}")

        return CPUInfo(
            model=model,
            cores=cores,
            threads=threads,
            frequency_ghz=frequency_ghz,
            architecture=architecture,
            features=features,
        )

    def detect_gpu(self) -> Optional[GPUInfo]:
        print("\n正在检测GPU信息...")
        try:
            if self.os == OS.WINDOWS:
                return self._detect_gpu_windows()
            elif self.os == OS.LINUX:
                return self._detect_gpu_linux()
            elif self.os == OS.MACOS:
                return self._detect_gpu_macos()
        except Exception as e:
            print(f"GPU检测失败: {e}")
            return None

    def _detect_gpu_windows(self) -> Optional[GPUInfo]:
        import wmi

        c = wmi.WMI()

        gpus = []
        for gpu in c.Win32_VideoController():
            if gpu.Name and "Microsoft Basic Display Adapter" not in gpu.Name:
                vendor = self._detect_gpu_vendor(gpu.Name)
                vram_gb = gpu.AdapterRAM / (1024**3) if gpu.AdapterRAM else 0.0
                gpus.append(
                    GPUInfo(
                        vendor=vendor,
                        model=gpu.Name,
                        vram_gb=vram_gb,
                        is_dedicated=vram_gb > 1.0,
                    )
                )

        if gpus:
            gpu = gpus[0]
            print(f"  GPU型号: {gpu.model}")
            print(f"  厂商: {gpu.vendor.value}")
            print(f"  显存: {gpu.vram_gb:.1f} GB")
            print(f"  类型: {'独立显卡' if gpu.is_dedicated else '集成显卡'}")
            return gpu

        print("  未检测到独立GPU")
        return None

    def _detect_gpu_linux(self) -> Optional[GPUInfo]:
        try:
            result = subprocess.run(
                ["lspci", "-nn"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stdout

                nvidia_match = re.search(
                    r"VGA.*NVIDIA.*\[(.+?)\].*?(\d+)MiB", output, re.IGNORECASE
                )
                if nvidia_match:
                    model = nvidia_match.group(1)
                    vram_gb = int(nvidia_match.group(2)) / 1024.0
                    print(f"  GPU型号: {model}")
                    print("  厂商: NVIDIA")
                    print(f"  显存: {vram_gb:.1f} GB")
                    print("  类型: 独立显卡")
                    return GPUInfo(
                        vendor=GPUVendor.NVIDIA, model=model, vram_gb=vram_gb
                    )

                amd_match = re.search(
                    r"VGA.*AMD.*\[(.+?)\].*?(\d+)MiB", output, re.IGNORECASE
                )
                if amd_match:
                    model = amd_match.group(1)
                    vram_gb = int(amd_match.group(2)) / 1024.0
                    print(f"  GPU型号: {model}")
                    print("  厂商: AMD")
                    print(f"  显存: {vram_gb:.1f} GB")
                    print("  类型: 独立显卡")
                    return GPUInfo(vendor=GPUVendor.AMD, model=model, vram_gb=vram_gb)

        except Exception as e:
            print(f"  Linux GPU检测失败: {e}")

        print("  未检测到独立GPU")
        return None

    def _detect_gpu_macos(self) -> Optional[GPUInfo]:
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("SPDisplaysDataType"):
                    gpu_data = data["SPDisplaysDataType"][0]
                    model = gpu_data.get("sppci_model", "Unknown")
                    vram_mb = gpu_data.get("sppci_vram_mb", 0)
                    vram_gb = vram_mb / 1024.0

                    print(f"  GPU型号: {model}")
                    print("  厂商: Apple")
                    print(f"  显存: {vram_gb:.1f} GB")
                    print(f"  类型: {'独立显卡' if vram_gb > 1.0 else '集成显卡'}")

                    return GPUInfo(
                        vendor=GPUVendor.APPLE,
                        model=model,
                        vram_gb=vram_gb,
                        is_dedicated=vram_gb > 1.0,
                    )

        except Exception as e:
            print(f"  macOS GPU检测失败: {e}")

        print("  未检测到独立GPU")
        return None

    def _detect_gpu_vendor(self, gpu_name: str) -> GPUVendor:
        gpu_name_lower = gpu_name.lower()
        if (
            "nvidia" in gpu_name_lower
            or "geforce" in gpu_name_lower
            or "rtx" in gpu_name_lower
        ):
            return GPUVendor.NVIDIA
        elif "amd" in gpu_name_lower or "radeon" in gpu_name_lower:
            return GPUVendor.AMD
        elif "intel" in gpu_name_lower:
            return GPUVendor.INTEL
        else:
            return GPUVendor.UNKNOWN

    def detect_memory(self) -> MemoryInfo:
        print("\n正在检测内存信息...")
        try:
            if self.os == OS.WINDOWS:
                return self._detect_memory_windows()
            elif self.os == OS.LINUX:
                return self._detect_memory_linux()
            elif self.os == OS.MACOS:
                return self._detect_memory_macos()
        except Exception as e:
            print(f"内存检测失败: {e}")
            return MemoryInfo(total_gb=8.0, available_gb=4.0, type="DDR4")

    def _detect_memory_windows(self) -> MemoryInfo:
        import psutil

        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)

        memory_type = "DDR4"
        speed_mhz = None

        try:
            import wmi

            c = wmi.WMI()
            for mem_module in c.Win32_PhysicalMemory():
                if mem_module.Speed:
                    speed_mhz = mem_module.Speed
                if mem_module.MemoryType:
                    memory_types = {
                        0: "Unknown",
                        1: "Other",
                        2: "DRAM",
                        3: "Synchronous DRAM",
                        4: "Cache DRAM",
                        5: "EDO",
                        6: "EDRAM",
                        7: "VRAM",
                        8: "SRAM",
                        9: "RAM",
                        10: "ROM",
                        11: "Flash",
                        12: "EEPROM",
                        13: "FEPROM",
                        14: "EPROM",
                        15: "CDRAM",
                        16: "3DRAM",
                        17: "SDRAM",
                        18: "SGRAM",
                        19: "RDRAM",
                        20: "DDR",
                        21: "DDR2",
                        22: "DDR2 FB-DIMM",
                        24: "DDR3",
                        26: "DDR4",
                        27: "DDR5",
                    }
                    memory_type = memory_types.get(mem_module.MemoryType, "Unknown")
                break

        except Exception as e:
            print(f"  获取内存类型失败: {e}")

        print(f"  总内存: {total_gb:.1f} GB")
        print(f"  可用内存: {available_gb:.1f} GB")
        print(f"  内存类型: {memory_type}")
        if speed_mhz:
            print(f"  内存频率: {speed_mhz:.0f} MHz")

        return MemoryInfo(
            total_gb=total_gb,
            available_gb=available_gb,
            type=memory_type,
            speed_mhz=speed_mhz,
        )

    def _detect_memory_linux(self) -> MemoryInfo:
        import psutil

        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)

        memory_type = "DDR4"
        speed_mhz = None

        try:
            result = subprocess.run(
                ["sudo", "dmidecode", "-t", "memory"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                output = result.stdout
                type_match = re.search(r"Type: (.+)", output)
                if type_match:
                    memory_type = type_match.group(1).strip()
                speed_match = re.search(r"Speed: (\d+) MHz", output)
                if speed_match:
                    speed_mhz = float(speed_match.group(1))
        except Exception as e:
            print(f"  获取内存类型失败: {e}")

        print(f"  总内存: {total_gb:.1f} GB")
        print(f"  可用内存: {available_gb:.1f} GB")
        print(f"  内存类型: {memory_type}")
        if speed_mhz:
            print(f"  内存频率: {speed_mhz:.0f} MHz")

        return MemoryInfo(
            total_gb=total_gb,
            available_gb=available_gb,
            type=memory_type,
            speed_mhz=speed_mhz,
        )

    def _detect_memory_macos(self) -> MemoryInfo:
        import psutil

        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)

        memory_type = "DDR4"
        speed_mhz = None

        try:
            result = subprocess.run(
                ["system_profiler", "SPMemoryDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("SPMemoryDataType"):
                    mem_data = data["SPMemoryDataType"][0]
                    memory_type = mem_data.get("dimm_type", "Unknown")
        except Exception as e:
            print(f"  获取内存类型失败: {e}")

        print(f"  总内存: {total_gb:.1f} GB")
        print(f"  可用内存: {available_gb:.1f} GB")
        print(f"  内存类型: {memory_type}")

        return MemoryInfo(
            total_gb=total_gb,
            available_gb=available_gb,
            type=memory_type,
            speed_mhz=speed_mhz,
        )

    def detect_all(self) -> HardwareInfo:
        print("=" * 80)
        print("开始硬件检测")
        print("=" * 80)

        cpu = self.detect_cpu()
        gpu = self.detect_gpu()
        memory = self.detect_memory()

        print("\n" + "=" * 80)
        print("硬件检测完成")
        print("=" * 80)

        return HardwareInfo(os=self.os, cpu=cpu, gpu=gpu, memory=memory)


class LlamaCppConfigOptimizer:
    def __init__(self, hardware: HardwareInfo, config_path: Optional[str] = None):
        self.hardware = hardware
        self.config_path = config_path
        self.current_config = None
        if config_path:
            self._load_current_config()

    def _load_current_config(self) -> None:
        """加载当前配置文件"""
        if not self.config_path or not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if config_data and "local_llm" in config_data:
                llm_config = config_data["local_llm"]
                self.current_config = {
                    "n_threads": llm_config.get("n_threads"),
                    "n_batch": llm_config.get("n_batch"),
                    "n_ctx": llm_config.get("n_ctx"),
                    "n_gpu_layers": llm_config.get("n_gpu_layers"),
                    "use_mmap": llm_config.get("use_mmap", True),
                    "use_mlock": llm_config.get("use_mlock", False),
                }
                print(f"已加载配置文件: {self.config_path}")
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def validate_current_config(
        self, recommended_config: LlamaCppConfig
    ) -> ConfigValidation:
        """验证当前配置并提供建议"""
        issues = []
        warnings = []
        suggestions = []

        if not self.current_config:
            return ConfigValidation(
                is_valid=True, issues=[], warnings=[], suggestions=[]
            )

        cpu = self.hardware.cpu
        gpu = self.hardware.gpu

        current_n_threads = self.current_config.get("n_threads")
        if current_n_threads:
            if current_n_threads > cpu.threads:
                issues.append(
                    f"线程数 ({current_n_threads}) 超过CPU逻辑线程数 "
                    f"({cpu.threads})，可能导致性能下降"
                )
            elif current_n_threads == cpu.threads:
                warnings.append(
                    f"线程数 ({current_n_threads}) 等于CPU逻辑线程数，"
                    f"建议预留1个线程给系统"
                )

        current_n_batch = self.current_config.get("n_batch")
        if current_n_batch:
            if gpu and gpu.vram_gb >= 8.0 and current_n_batch < 256:
                suggestions.append(
                    f"GPU显存充足 ({gpu.vram_gb:.1f}GB)，"
                    f"建议增加批处理大小到256或512以提升吞吐量"
                )
            elif not gpu and current_n_batch > 256:
                warnings.append(
                    f"无独立GPU，批处理大小 ({current_n_batch}) 较大，可能占用过多内存"
                )

        current_n_ctx = self.current_config.get("n_ctx")
        if current_n_ctx:
            if current_n_ctx > 8192:
                warnings.append(f"上下文窗口 ({current_n_ctx}) 较大，将占用更多内存")
            if current_n_ctx < 2048:
                suggestions.append(
                    f"上下文窗口 ({current_n_ctx}) 较小，"
                    f"对于长文本生成建议增加到4096或8192"
                )

        current_n_gpu_layers = self.current_config.get("n_gpu_layers")
        if current_n_gpu_layers is not None:
            if gpu and gpu.vram_gb >= 8.0 and current_n_gpu_layers == 0:
                issues.append(
                    f"GPU显存充足 ({gpu.vram_gb:.1f}GB)，"
                    f"但GPU层数设置为0，建议启用GPU加速"
                )
            elif gpu and gpu.vram_gb < 4.0 and current_n_gpu_layers > 30:
                warnings.append(
                    f"GPU显存较小 ({gpu.vram_gb:.1f}GB)，"
                    f"GPU层数 ({current_n_gpu_layers}) 可能导致显存不足"
                )

        is_valid = len(issues) == 0

        return ConfigValidation(
            is_valid=is_valid, issues=issues, warnings=warnings, suggestions=suggestions
        )

    def compare_configs(self, recommended_config: LlamaCppConfig) -> None:
        """对比当前配置和推荐配置"""
        if not self.current_config:
            print("\n未找到当前配置文件，跳过对比")
            return

        print("\n" + "=" * 80)
        print("配置对比")
        print("=" * 80)

        print(f"\n{'参数':<25} {'当前配置':<15} {'推荐配置':<15} {'状态'}")
        print("-" * 80)

        params = [
            ("线程数 (-t)", "n_threads", recommended_config.n_threads),
            ("批处理大小 (-b)", "n_batch", recommended_config.n_batch),
            ("上下文窗口 (-c)", "n_ctx", recommended_config.n_ctx),
            ("GPU层数 (-ngl)", "n_gpu_layers", recommended_config.n_gpu_layers),
            ("内存映射", "use_mmap", recommended_config.use_mmap),
            ("内存锁定", "use_mlock", recommended_config.use_mlock),
        ]

        for param_name, config_key, recommended_value in params:
            current_value = self.current_config.get(config_key)
            if current_value is None:
                status = "未设置"
            elif current_value == recommended_value:
                status = "✅ 匹配"
            else:
                status = "⚠️ 差异"

            current_str = str(current_value) if current_value is not None else "未设置"
            recommended_str = str(recommended_value)

            print(f"{param_name:<25} {current_str:<15} {recommended_str:<15} {status}")

        validation = self.validate_current_config(recommended_config)

        if validation.issues:
            print("\n" + "=" * 80)
            print("配置问题")
            print("=" * 80)
            for i, issue in enumerate(validation.issues, 1):
                print(f"  ❌ {i}. {issue}")

        if validation.warnings:
            print("\n" + "=" * 80)
            print("配置警告")
            print("=" * 80)
            for i, warning in enumerate(validation.warnings, 1):
                print(f"  ⚠️ {i}. {warning}")

        if validation.suggestions:
            print("\n" + "=" * 80)
            print("优化建议")
            print("=" * 80)
            for i, suggestion in enumerate(validation.suggestions, 1):
                print(f"  💡 {i}. {suggestion}")

    def recommend_config(self) -> ConfigRecommendation:
        print("\n" + "=" * 80)
        print("生成llama-cpp配置推荐")
        print("=" * 80)

        reasoning = []
        config = self._calculate_optimal_config(reasoning)
        performance = self._estimate_performance(config)
        command = self._generate_command(config)

        print("\n推荐配置:")
        print("-" * 80)
        print(f"  线程数数 (-t): {config.n_threads}")
        print(f"  批处理大小 (-b): {config.n_batch}")
        print(f"  上下文窗口 (-c): {config.n_ctx}")
        print(f"  GPU层数 (-ngl): {config.n_gpu_layers}")
        print(f"  量化级别: {config.quantization}")
        print(f"  内存映射: {'启用' if config.use_mmap else '禁用'}")
        print(f"  内存锁定: {'启用' if config.use_mlock else '禁用'}")
        print(f"  低显存模式: {'启用' if config.low_vram else '禁用'}")

        print("\n推荐依据:")
        print("-" * 80)
        for i, reason in enumerate(reasoning, 1):
            print(f"  {i}. {reason}")

        print("\n性能预期:")
        print("-" * 80)
        print(f"  {performance}")

        print("\n命令行示例:")
        print("-" * 80)
        print(command)

        return ConfigRecommendation(
            config=config,
            reasoning=reasoning,
            performance_expectation=performance,
            command_template=command,
        )

    def _calculate_optimal_config(self, reasoning: List[str]) -> LlamaCppConfig:
        cpu = self.hardware.cpu
        gpu = self.hardware.gpu
        memory = self.hardware.memory

        n_threads = self._calculate_threads(cpu, reasoning)
        n_batch = self._calculate_batch_size(cpu, gpu, reasoning)
        n_ctx = self._calculate_context_size(memory, gpu, reasoning)
        n_gpu_layers = self._calculate_gpu_layers(gpu, reasoning)
        quantization = self._calculate_quantization(memory, gpu, reasoning)
        use_mmap = self._should_use_mmap(memory, reasoning)
        use_mlock = self._should_use_mlock(self.hardware.os, reasoning)
        low_vram = self._should_use_low_vram(gpu, memory, reasoning)
        split_mode = self._calculate_split_mode(gpu, reasoning)

        return LlamaCppConfig(
            n_threads=n_threads,
            n_batch=n_batch,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            quantization=quantization,
            use_mmap=use_mmap,
            use_mlock=use_mlock,
            low_vram=low_vram,
            split_mode=split_mode,
        )

    def _calculate_threads(self, cpu: CPUInfo, reasoning: List[str]) -> int:
        n_threads = max(1, cpu.threads - 1)
        reasoning.append(
            f"线程数设置为{n_threads}（CPU逻辑线程数{cpu.threads}，预留1个线程给系统）"
        )
        return n_threads

    def _calculate_batch_size(
        self, cpu: CPUInfo, gpu: Optional[GPUInfo], reasoning: List[str]
    ) -> int:
        if gpu and gpu.vram_gb >= 8.0:
            n_batch = 512
            reasoning.append(
                f"批处理大小设置为{n_batch}（GPU显存充足{gpu.vram_gb:.1f}GB，使用较大批次提升吞吐量）"
            )
        elif gpu and gpu.vram_gb >= 4.0:
            n_batch = 256
            reasoning.append(
                f"批处理大小设置为{n_batch}（GPU显存适中{gpu.vram_gb:.1f}GB，平衡性能和显存使用）"
            )
        else:
            n_batch = 128
            reasoning.append(
                f"批处理大小设置为{n_batch}（无独立GPU或显存较小，使用较小批次减少内存占用）"
            )

        return n_batch

    def _calculate_context_size(
        self, memory: MemoryInfo, gpu: Optional[GPUInfo], reasoning: List[str]
    ) -> int:
        if gpu and gpu.vram_gb >= 16.0:
            n_ctx = 8192
            reasoning.append(
                f"上下文窗口设置为{n_ctx}（GPU显存充足{gpu.vram_gb:.1f}GB，支持长上下文）"
            )
        elif gpu and gpu.vram_gb >= 8.0:
            n_ctx = 4096
            reasoning.append(
                f"上下文窗口设置为{n_ctx}（GPU显存适中{gpu.vram_gb:.1f}GB，标准上下文长度）"
            )
        elif memory.total_gb >= 32.0:
            n_ctx = 4096
            reasoning.append(
                f"上下文窗口设置为{n_ctx}（内存充足{memory.total_gb:.1f}GB，标准上下文长度）"
            )
        else:
            n_ctx = 2048
            reasoning.append(
                f"上下文窗口设置为{n_ctx}（内存有限{memory.total_gb:.1f}GB，使用较短上下文）"
            )

        return n_ctx

    def _calculate_gpu_layers(
        self, gpu: Optional[GPUInfo], reasoning: List[str]
    ) -> int:
        if not gpu:
            n_gpu_layers = 0
            reasoning.append("GPU层数设置为0（未检测到独立GPU，使用纯CPU推理）")
        elif gpu.vram_gb >= 16.0:
            n_gpu_layers = 99
            reasoning.append(
                f"GPU层数设置为{n_gpu_layers}（GPU显存充足{gpu.vram_gb:.1f}GB，将所有层加载到GPU）"
            )
        elif gpu.vram_gb >= 8.0:
            n_gpu_layers = 50
            reasoning.append(
                f"GPU层数设置为{n_gpu_layers}（GPU显存适中{gpu.vram_gb:.1f}GB，将部分层加载到GPU）"
            )
        elif gpu.vram_gb >= 4.0:
            n_gpu_layers = 30
            reasoning.append(
                f"GPU层数设置为{n_gpu_layers}（GPU显存较小{gpu.vram_gb:.1f}GB，仅将部分层加载到GPU）"
            )
        else:
            n_gpu_layers = 0
            reasoning.append(
                f"GPU层数设置为0（GPU显存不足{gpu.vram_gb:.1f}GB，使用纯CPU推理）"
            )

        return n_gpu_layers

    def _calculate_quantization(
        self, memory: MemoryInfo, gpu: Optional[GPUInfo], reasoning: List[str]
    ) -> str:
        if gpu and gpu.vram_gb >= 16.0:
            quantization = "Q4_K_M"
            reasoning.append(
                f"量化级别设置为{quantization}（GPU显存充足{gpu.vram_gb:.1f}GB，使用Q4量化平衡质量和速度）"
            )
        elif gpu and gpu.vram_gb >= 8.0:
            quantization = "Q4_K_M"
            reasoning.append(
                f"量化级别设置为{quantization}（GPU显存适中{gpu.vram_gb:.1f}GB，使用Q4量化）"
            )
        elif memory.total_gb >= 32.0:
            quantization = "Q4_K_M"
            reasoning.append(
                f"量化级别设置为{quantization}（内存充足{memory.total_gb:.1f}GB，使用Q4量化）"
            )
        elif memory.total_gb >= 16.0:
            quantization = "Q5_K_M"
            reasoning.append(
                f"量化级别设置为{quantization}（内存适中{memory.total_gb:.1f}GB，使用Q5量化提升质量）"
            )
        else:
            quantization = "Q6_K"
            reasoning.append(
                f"量化级别设置为{quantization}（内存有限{memory.total_gb:.1f}GB，使用Q6量化减少内存占用）"
            )

        return quantization

    def _should_use_mmap(self, memory: MemoryInfo, reasoning: List[str]) -> bool:
        use_mmap = memory.total_gb >= 8.0
        if use_mmap:
            reasoning.append(
                f"启用内存映射（内存{memory.total_gb:.1f}GB充足，mmap可减少内存占用）"
            )
        else:
            reasoning.append(
                f"禁用内存映射（内存{memory.total_gb:.1f}GB有限，避免频繁I/O）"
            )

        return use_mmap

    def _should_use_mlock(self, os: OS, reasoning: List[str]) -> bool:
        use_mlock = os != OS.WINDOWS
        if use_mlock:
            reasoning.append("启用内存锁定（非Windows系统，mlock可防止内存被交换）")
        else:
            reasoning.append("禁用内存锁定（Windows系统不支持mlock）")

        return use_mlock

    def _should_use_low_vram(
        self, gpu: Optional[GPUInfo], memory: MemoryInfo, reasoning: List[str]
    ) -> bool:
        if not gpu:
            low_vram = False
            reasoning.append("禁用低显存模式（未检测到GPU）")
        elif gpu.vram_gb >= 8.0:
            low_vram = False
            reasoning.append(f"禁用低显存模式（GPU显存充足{gpu.vram_gb:.1f}GB）")
        else:
            low_vram = True
            reasoning.append(
                f"启用低显存模式（GPU显存较小{gpu.vram_gb:.1f}GB，减少显存占用）"
            )

        return low_vram

    def _calculate_split_mode(
        self, gpu: Optional[GPUInfo], reasoning: List[str]
    ) -> Optional[str]:
        if not gpu:
            return None

        if gpu.vendor == GPUVendor.NVIDIA and gpu.vram_gb >= 8.0:
            split_mode = "layer"
            reasoning.append(
                f"使用分层分割模式（NVIDIA GPU显存充足{gpu.vram_gb:.1f}GB，"
                f"分层分割优化性能）"
            )
            return split_mode

        return None

    def _estimate_performance(self, config: LlamaCppConfig) -> str:
        gpu = self.hardware.gpu
        cpu = self.hardware.cpu

        if gpu and config.n_gpu_layers > 0:
            if gpu.vram_gb >= 16.0:
                return "高性能：GPU加速推理，预期生成速度30-50 tokens/秒，适合实时对话"
            elif gpu.vram_gb >= 8.0:
                return (
                    "中高性能：GPU+CPU混合推理，"
                    "预期生成速度20-30 tokens/秒，适合交互式应用"
                )
            else:
                return (
                    "中等性能：GPU辅助推理，预期生成速度10-20 tokens/秒，适合批处理任务"
                )
        else:
            if cpu.threads >= 8:
                return "中等性能：纯CPU推理，预期生成速度5-10 tokens/秒，适合离线处理"
            else:
                return "基础性能：纯CPU推理，预期生成速度2-5 tokens/秒，适合小规模测试"

    def _generate_command(self, config: LlamaCppConfig) -> str:
        command_parts = ["llama-cli"]

        command_parts.append("-m model.gguf")
        command_parts.append(f"-t {config.n_threads}")
        command_parts.append(f"-b {config.n_batch}")
        command_parts.append(f"-c {config.n_ctx}")
        command_parts.append(f"-ngl {config.n_gpu_layers}")

        if config.use_mmap:
            command_parts.append("--mmap")
        if config.use_mlock:
            command_parts.append("--mlock")
        if config.low_vram:
            command_parts.append("--low-vram")
        if config.split_mode:
            command_parts.append(f"--split-mode {config.split_mode}")

        command = " ".join(command_parts)

        return command


def main():
    import argparse

    parser = argparse.ArgumentParser(description="llama-cpp 配置优化器")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config.yaml",
        help="配置文件路径（默认：config.yaml）",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("llama-cpp 配置优化器")
    print("=" * 80)
    print()

    try:
        detector = HardwareDetector()
        hardware = detector.detect_all()

        config_path = args.config
        if os.path.exists(config_path):
            print(f"\n使用配置文件: {config_path}")
        else:
            print(f"\n配置文件不存在: {config_path}")
            print("将仅显示推荐配置，不进行对比")

        optimizer = LlamaCppConfigOptimizer(hardware, config_path)
        recommendation = optimizer.recommend_config()

        if optimizer.current_config:
            optimizer.compare_configs(recommendation.config)

        print("\n" + "=" * 80)
        print("配置推荐完成")
        print("=" * 80)

        print("\n提示:")
        print("-" * 80)
        print("1. 请将 'model.gguf' 替换为实际的模型文件路径")
        print("2. 根据实际需求调整上下文窗口大小 (-c)")
        print("3. 如果遇到内存不足，可以减小批处理大小 (-b) 或上下文窗口 (-c)")
        print("4. 对于长文本生成，建议增加上下文窗口大小")
        print("5. 对于实时对话，建议使用较小的批处理大小以降低延迟")
        print("6. 使用 --config 参数指定不同的配置文件")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
