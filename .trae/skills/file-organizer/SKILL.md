---
name: file-organizer
description: A comprehensive file organization tool that helps users organize files based on various criteria like file type, date, size, and custom rules.
version: 1.0.0
author: ConsensusWeaverAgent
category: Productivity
platforms: [Windows, macOS, Linux]
---

# File Organizer Skill

## 1. Overview

### 1.1 Skill Description
The File Organizer skill is a comprehensive tool designed to help users organize files in their system based on various criteria. It provides a systematic approach to file management, allowing users to automatically sort, categorize, and arrange files according to predefined or custom rules.

### 1.2 Key Features
- Organize files by type (documents, images, videos, audio, etc.)
- Organize files by date (creation date, modification date)
- Organize files by size (small, medium, large)
- Organize files by name (alphabetical, reverse alphabetical)
- Create custom organization rules
- Preview organization results before execution
- Undo organization operations
- Generate organization reports

### 1.3 Use Cases
- Cleaning up cluttered download folders
- Organizing project files
- Sorting photos and videos by date
- Managing document libraries
- Preparing files for backup or archiving

## 2. Interface Specification

### 2.1 Input Parameters

#### Organize by Type
```json
{
  "action": "organize_by_type",
  "source_directory": "path/to/source/folder",
  "target_directory": "path/to/target/folder",
  "file_types": ["documents", "images", "videos", "audio", "archives"],
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

#### Organize by Date
```json
{
  "action": "organize_by_date",
  "source_directory": "path/to/source/folder",
  "target_directory": "path/to/target/folder",
  "date_type": "modification", // or "creation"
  "date_format": "YYYY-MM-DD", // or "YYYY/MM/DD", "YYYY-MM", etc.
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

#### Organize by Size
```json
{
  "action": "organize_by_size",
  "source_directory": "path/to/source/folder",
  "target_directory": "path/to/target/folder",
  "size_ranges": {
    "small": "10MB",
    "medium": "100MB",
    "large": "1GB"
  },
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

#### Organize by Name
```json
{
  "action": "organize_by_name",
  "source_directory": "path/to/source/folder",
  "target_directory": "path/to/target/folder",
  "sort_order": "ascending", // or "descending"
  "group_by_initial": true,
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

#### Custom Organization
```json
{
  "action": "organize_custom",
  "source_directory": "path/to/source/folder",
  "target_directory": "path/to/target/folder",
  "rules": [
    {
      "pattern": "*.pdf",
      "destination": "documents/pdfs",
      "description": "PDF documents"
    },
    {
      "pattern": "*.jpg",
      "destination": "images/jpeg",
      "description": "JPEG images"
    }
  ],
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

#### Undo Operation
```json
{
  "action": "undo",
  "operation_id": "unique-operation-id"
}
```

#### Generate Report
```json
{
  "action": "generate_report",
  "operation_id": "unique-operation-id",
  "format": "json" // or "text", "csv"
}
```

### 2.2 Output Format

#### Success Response
```json
{
  "status": "success",
  "operation_id": "unique-operation-id",
  "message": "Files organized successfully",
  "details": {
    "total_files": 42,
    "organized_files": 38,
    "skipped_files": 4,
    "directories_created": 12,
    "execution_time": 2.45
  },
  "preview": [
    {
      "source": "path/to/source/file1.txt",
      "destination": "path/to/target/texts/file1.txt",
      "status": "to_be_moved"
    }
  ]
}
```

#### Error Response
```json
{
  "status": "error",
  "message": "Error organizing files",
  "error_code": "INVALID_PATH",
  "details": {
    "invalid_path": "path/to/nonexistent/folder"
  },
  "suggestions": [
    "Check if the source directory exists",
    "Verify you have permissions to access the directory"
  ]
}
```

## 3. Core Functionality

### 3.1 File Type Organization
- **Document Types**: .txt, .doc, .docx, .pdf, .odt, .rtf
- **Image Types**: .jpg, .jpeg, .png, .gif, .bmp, .svg
- **Video Types**: .mp4, .avi, .mov, .wmv, .flv
- **Audio Types**: .mp3, .wav, .ogg, .flac, .aac
- **Archive Types**: .zip, .rar, .7z, .tar, .gz
- **Code Types**: .py, .js, .java, .c, .cpp, .html, .css

### 3.2 Date Organization
- **Creation Date**: Organizes files based on when they were created
- **Modification Date**: Organizes files based on when they were last modified
- **Date Formats**: 
  - YYYY-MM-DD (e.g., 2026-01-30)
  - YYYY/MM/DD (e.g., 2026/01/30)
  - YYYY-MM (e.g., 2026-01)
  - YYYY (e.g., 2026)

### 3.3 Size Organization
- **Small Files**: Less than specified size (default: 10MB)
- **Medium Files**: Between small and large size (default: 10MB - 100MB)
- **Large Files**: Larger than specified size (default: 100MB)

### 3.4 Name Organization
- **Alphabetical Order**: A-Z
- **Reverse Alphabetical Order**: Z-A
- **Group by Initial**: Creates subdirectories for each initial letter

### 3.5 Custom Rules
- **File Patterns**: Support for wildcards (*.txt) and regex patterns
- **Destination Paths**: Relative or absolute paths
- **Rule Priority**: Rules are applied in the order they are defined

## 4. Error Handling

### 4.1 Error Codes
| Error Code | Description | Suggestion |
|------------|-------------|------------|
| INVALID_PATH | Source or target directory does not exist | Check if the directory path is correct and exists |
| PERMISSION_DENIED | Insufficient permissions to access directories | Run the tool with appropriate permissions |
| FILE_LOCKED | Some files are locked and cannot be moved | Close any applications using the files and try again |
| INVALID_PARAMETER | One or more parameters are invalid | Check the parameter values and format |
| OPERATION_FAILED | General operation failure | Check the error details and try again |
| UNDO_NOT_AVAILABLE | No undo information available for the operation | Ensure the operation was completed successfully and try again |

### 4.2 Error Handling Strategies
1. **Graceful Degradation**: If some files cannot be processed, continue with the rest
2. **Detailed Error Reports**: Provide specific information about failed operations
3. **Rollback Capability**: Ability to undo operations if errors occur
4. **Validation**: Validate input parameters before executing operations
5. **Retry Logic**: Automatically retry failed operations with appropriate backoff

## 5. Usage Instructions

### 5.1 Basic Usage

#### Organize Files by Type
```bash
# Example: Organize files in Downloads folder by type
file-organizer --action organize_by_type \
  --source "C:\Users\User\Downloads" \
  --target "C:\Users\User\Organized" \
  --file-types documents images videos audio \
  --preview-only
```

#### Organize Files by Date
```bash
# Example: Organize photos by creation date
file-organizer --action organize_by_date \
  --source "D:\Photos" \
  --target "D:\Organized Photos" \
  --date-type creation \
  --date-format "YYYY-MM" \
  --move-files
```

#### Organize Files by Size
```bash
# Example: Organize files by size
file-organizer --action organize_by_size \
  --source "E:\Files" \
  --target "E:\Organized Files" \
  --size-ranges "{\"small\": \"5MB\", \"medium\": \"50MB\", \"large\": \"500MB\"}" \
  --preview-only
```

#### Organize Files by Name
```bash
# Example: Organize documents by name
file-organizer --action organize_by_name \
  --source "F:\Documents" \
  --target "F:\Organized Documents" \
  --sort-order ascending \
  --group-by-initial \
  --move-files
```

#### Custom Organization
```bash
# Example: Custom organization with rules
file-organizer --action organize_custom \
  --source "G:\Projects" \
  --target "G:\Organized Projects" \
  --rules "[{\"pattern\": \"*.py\", \"destination\": \"python\", \"description\": \"Python files\"}, {\"pattern\": \"*.js\", \"destination\": \"javascript\", \"description\": \"JavaScript files\"}]" \
  --preview-only
```

### 5.2 Advanced Usage

#### Combining Multiple Organization Methods
```bash
# Example: First by date, then by type
# Step 1: Organize by date
file-organizer --action organize_by_date \
  --source "C:\Users\User\Photos" \
  --target "C:\Users\User\Organized Photos" \
  --date-type creation \
  --date-format "YYYY-MM"

# Step 2: Organize each date folder by type
file-organizer --action organize_by_type \
  --source "C:\Users\User\Organized Photos" \
  --target "C:\Users\User\Organized Photos" \
  --file-types images videos \
  --move-files
```

#### Using Wildcards in Custom Rules
```bash
# Example: Organize files with specific patterns
file-organizer --action organize_custom \
  --source "D:\Files" \
  --target "D:\Organized Files" \
  --rules "[{\"pattern\": \"report_*.pdf\", \"destination\": \"reports\", \"description\": \"PDF reports\"}, {\"pattern\": \"backup_*.zip\", \"destination\": \"backups\", \"description\": \"Backup archives\"}]" \
  --move-files
```

#### Undoing an Operation
```bash
# Example: Undo the last organization operation
file-organizer --action undo \
  --operation-id "20260130-123456-789"
```

#### Generating a Report
```bash
# Example: Generate a report for an operation
file-organizer --action generate_report \
  --operation-id "20260130-123456-789" \
  --format json
```

## 6. Testing

### 6.1 Test Cases

#### Test Case 1: Organize by Type
**Input**:
```json
{
  "action": "organize_by_type",
  "source_directory": "test/fixtures/mixed_files",
  "target_directory": "test/output/organized_by_type",
  "file_types": ["documents", "images", "videos"],
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

**Expected Output**:
```json
{
  "status": "success",
  "operation_id": "test-operation-001",
  "message": "Files organized successfully",
  "details": {
    "total_files": 10,
    "organized_files": 10,
    "skipped_files": 0,
    "directories_created": 3,
    "execution_time": 0.5
  },
  "preview": [
    {
      "source": "test/fixtures/mixed_files/doc1.pdf",
      "destination": "test/output/organized_by_type/documents/doc1.pdf",
      "status": "to_be_moved"
    },
    {
      "source": "test/fixtures/mixed_files/image1.jpg",
      "destination": "test/output/organized_by_type/images/image1.jpg",
      "status": "to_be_moved"
    },
    {
      "source": "test/fixtures/mixed_files/video1.mp4",
      "destination": "test/output/organized_by_type/videos/video1.mp4",
      "status": "to_be_moved"
    }
  ]
}
```

#### Test Case 2: Organize by Date
**Input**:
```json
{
  "action": "organize_by_date",
  "source_directory": "test/fixtures/date_files",
  "target_directory": "test/output/organized_by_date",
  "date_type": "modification",
  "date_format": "YYYY-MM",
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

**Expected Output**:
```json
{
  "status": "success",
  "operation_id": "test-operation-002",
  "message": "Files organized successfully",
  "details": {
    "total_files": 6,
    "organized_files": 6,
    "skipped_files": 0,
    "directories_created": 2,
    "execution_time": 0.3
  },
  "preview": [
    {
      "source": "test/fixtures/date_files/file_20260101.txt",
      "destination": "test/output/organized_by_date/2026-01/file_20260101.txt",
      "status": "to_be_moved"
    },
    {
      "source": "test/fixtures/date_files/file_20260201.txt",
      "destination": "test/output/organized_by_date/2026-02/file_20260201.txt",
      "status": "to_be_moved"
    }
  ]
}
```

#### Test Case 3: Custom Organization
**Input**:
```json
{
  "action": "organize_custom",
  "source_directory": "test/fixtures/custom_files",
  "target_directory": "test/output/organized_custom",
  "rules": [
    {
      "pattern": "*.pdf",
      "destination": "documents/pdfs",
      "description": "PDF documents"
    },
    {
      "pattern": "*.jpg",
      "destination": "images/jpeg",
      "description": "JPEG images"
    }
  ],
  "options": {
    "create_subdirectories": true,
    "move_files": false,
    "overwrite_existing": false,
    "preview_only": true
  }
}
```

**Expected Output**:
```json
{
  "status": "success",
  "operation_id": "test-operation-003",
  "message": "Files organized successfully",
  "details": {
    "total_files": 4,
    "organized_files": 4,
    "skipped_files": 0,
    "directories_created": 2,
    "execution_time": 0.2
  },
  "preview": [
    {
      "source": "test/fixtures/custom_files/doc1.pdf",
      "destination": "test/output/organized_custom/documents/pdfs/doc1.pdf",
      "status": "to_be_moved"
    },
    {
      "source": "test/fixtures/custom_files/image1.jpg",
      "destination": "test/output/organized_custom/images/jpeg/image1.jpg",
      "status": "to_be_moved"
    }
  ]
}
```

#### Test Case 4: Error Handling - Invalid Path
**Input**:
```json
{
  "action": "organize_by_type",
  "source_directory": "nonexistent/path",
  "target_directory": "test/output/organized",
  "file_types": ["documents"],
  "options": {
    "preview_only": true
  }
}
```

**Expected Output**:
```json
{
  "status": "error",
  "message": "Error organizing files",
  "error_code": "INVALID_PATH",
  "details": {
    "invalid_path": "nonexistent/path"
  },
  "suggestions": [
    "Check if the source directory exists",
    "Verify you have permissions to access the directory"
  ]
}
```

### 6.2 Test Environment Setup
1. **Create Test Directories**: Set up source directories with test files
2. **Prepare Test Files**: Create files of different types, sizes, and dates
3. **Configure Test Environment**: Ensure proper permissions and access rights
4. **Run Test Cases**: Execute each test case and verify results
5. **Clean Up**: Remove test output directories after testing

## 7. Implementation Details

### 7.1 Technical Architecture
- **Core Engine**: Responsible for executing file organization operations
- **File Scanner**: Scans source directories and collects file information
- **Rule Engine**: Processes organization rules and determines file destinations
- **File Manager**: Handles file operations (copy, move, rename)
- **Report Generator**: Creates operation reports and previews
- **Undo Manager**: Tracks operations for rollback capability

### 7.2 File Type Mapping
| Category | Extensions |
|----------|------------|
| Documents | .txt, .doc, .docx, .pdf, .odt, .rtf, .csv, .xls, .xlsx, .ppt, .pptx |
| Images | .jpg, .jpeg, .png, .gif, .bmp, .svg, .tiff, .webp |
| Videos | .mp4, .avi, .mov, .wmv, .flv, .mkv, .webm |
| Audio | .mp3, .wav, .ogg, .flac, .aac, .wma, .m4a |
| Archives | .zip, .rar, .7z, .tar, .gz, .bz2 |
| Code | .py, .js, .java, .c, .cpp, .h, .cs, .php, .html, .css |
| Executables | .exe, .msi, .app, .dmg, .sh, .bat |

### 7.3 Performance Considerations
1. **Parallel Processing**: Use multi-threading for scanning and processing files
2. **Batched Operations**: Process files in batches to reduce I/O overhead
3. **Caching**: Cache file metadata to avoid repeated disk access
4. **Progress Tracking**: Provide real-time progress updates for large operations
5. **Resource Management**: Limit simultaneous file operations to avoid system overload

### 7.4 Security Considerations
1. **File Permissions**: Preserve file permissions during operations
2. **Data Integrity**: Ensure files are not corrupted during move/copy operations
3. **Privacy**: Do not collect or transmit any file content
4. **Validation**: Validate all user inputs to prevent security vulnerabilities
5. **Error Handling**: Handle errors securely without exposing sensitive information

## 8. Integration Guidelines

### 8.1 Command Line Integration
```bash
# Installation
pip install file-organizer-skill

# Usage
file-organizer [OPTIONS] COMMAND [ARGS]
```

### 8.2 API Integration
```python
from file_organizer import FileOrganizer

# Initialize the organizer
organizer = FileOrganizer()

# Organize files by type
result = organizer.organize_by_type(
    source_directory="/path/to/source",
    target_directory="/path/to/target",
    file_types=["documents", "images"],
    preview_only=True
)

# Organize files by date
result = organizer.organize_by_date(
    source_directory="/path/to/source",
    target_directory="/path/to/target",
    date_type="modification",
    date_format="YYYY-MM-DD"
)

# Custom organization
result = organizer.organize_custom(
    source_directory="/path/to/source",
    target_directory="/path/to/target",
    rules=[
        {"pattern": "*.pdf", "destination": "documents/pdfs"},
        {"pattern": "*.jpg", "destination": "images/jpeg"}
    ]
)

# Undo operation
result = organizer.undo(operation_id="operation-123")

# Generate report
result = organizer.generate_report(
    operation_id="operation-123",
    format="json"
)
```

### 8.3 Automation Integration
The File Organizer skill can be integrated with automation tools like:
- **Cron Jobs**: Schedule regular organization tasks
- **Task Scheduler**: Windows task scheduler integration
- **Automator**: macOS Automator integration
- **Alfred**: macOS Alfred workflow integration
- **Shortcuts**: iOS/iPadOS Shortcuts integration

## 9. Troubleshooting

### 9.1 Common Issues

#### Files Not Being Organized
**Possible Causes**:
- Incorrect source directory path
- Insufficient permissions
- Files are locked by other applications
- File patterns don't match any files

**Solutions**:
- Verify the source directory path
- Run as administrator/root
- Close applications using the files
- Check and adjust file patterns

#### Organization Taking Too Long
**Possible Causes**:
- Large number of files
- Slow disk I/O
- Network storage delays
- Insufficient system resources

**Solutions**:
- Process files in smaller batches
- Use local storage instead of network storage
- Close unnecessary applications
- Increase system resources if possible

#### Undo Operation Failing
**Possible Causes**:
- Operation ID not found
- Original files have been modified
- Target directory structure has changed
- Undo information has been cleared

**Solutions**:
- Verify the operation ID
- Ensure original files are intact
- Avoid modifying organized files before undoing
- Undo operations promptly after execution

### 9.2 Logging and Debugging
```bash
# Enable verbose logging
file-organizer --action organize_by_type \
  --source "path/to/source" \
  --target "path/to/target" \
  --verbose

# Enable debug logging
file-organizer --action organize_by_type \
  --source "path/to/source" \
  --target "path/to/target" \
  --debug
```

## 10. Conclusion

The File Organizer skill provides a comprehensive solution for file management, offering flexible organization options to suit various needs. Its modular design allows for easy extension and integration with other tools and workflows.

By following the guidelines and examples provided in this documentation, users can effectively organize their files, reduce clutter, and improve productivity. The skill's robust error handling and undo capabilities ensure that operations can be performed safely and reliably.

Whether used as a standalone tool or integrated into a larger workflow, the File Organizer skill is a valuable asset for anyone looking to maintain a well-organized digital workspace.
