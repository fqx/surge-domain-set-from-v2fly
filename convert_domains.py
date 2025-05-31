#!/usr/bin/env python3
import os
import re
import shutil
from pathlib import Path

class DomainConverter:
    def __init__(self, source_dir, output_dir):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.processed_includes = set()
        
    def convert_all_files(self):
        """Convert all files in the source directory"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process all files in source directory
        for file_path in self.source_dir.glob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                self.convert_file(file_path.name)
    
    def convert_file(self, filename):
        """Convert a single file from v2fly format to Surge domain-set format"""
        source_file = self.source_dir / filename
        output_file = self.output_dir / filename
        
        if not source_file.exists():
            print(f"Warning: Source file {source_file} does not exist")
            return
        
        print(f"Converting {filename}...")
        
        # Reset processed includes for each file
        self.processed_includes = set()
        
        with open(source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        converted_lines = self.process_lines(lines, filename)
        
        # Write converted content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(converted_lines)
        
        print(f"Converted {filename} -> {output_file}")
    
    def process_lines(self, lines, current_file):
        """Process lines according to conversion rules"""
        converted_lines = []
        
        for line in lines:
            line = line.rstrip('\n\r')
            
            # Skip empty lines
            if not line.strip():
                converted_lines.append('\n')
                continue
            
            # Keep comments
            if line.strip().startswith('#'):
                converted_lines.append(line + '\n')
                continue
            
            # Handle includes
            if line.strip().startswith('include:'):
                include_file = line.strip()[8:].strip()
                include_lines = self.process_include(include_file, current_file)
                converted_lines.extend(include_lines)
                continue
            
            # Process domain entries
            converted_line = self.convert_domain_line(line)
            if converted_line:
                converted_lines.append(converted_line + '\n')
        
        return converted_lines
    
    def process_include(self, include_file, current_file):
        """Process include files recursively"""
        # Prevent infinite recursion
        include_key = f"{current_file}:{include_file}"
        if include_key in self.processed_includes:
            print(f"Warning: Circular include detected for {include_file} in {current_file}")
            return []
        
        self.processed_includes.add(include_key)
        
        include_path = self.source_dir / include_file
        if not include_path.exists():
            print(f"Warning: Include file {include_file} not found")
            return []
        
        print(f"Processing include: {include_file}")
        
        with open(include_path, 'r', encoding='utf-8') as f:
            include_lines = f.readlines()
        
        # Add a comment to show where the included content comes from
        result = [f"# Included from {include_file}\n"]
        result.extend(self.process_lines(include_lines, include_file))
        result.append(f"# End of {include_file}\n")
        
        return result
    
    def convert_domain_line(self, line):
        """Convert a single domain line according to rules"""
        line = line.strip()
        
        # Remove attributes (everything after @)
        if '@' in line:
            line = line.split('@')[0].strip()
        
        # Skip keyword: lines (not supported by Surge)
        if line.startswith('keyword:'):
            return None
        
        # Skip regexp: lines (not supported by Surge)
        if line.startswith('regexp:'):
            return None
        
        # Handle domain: prefix
        if line.startswith('domain:'):
            domain = line[7:].strip()
            return f".{domain}"
        
        # Handle full: prefix
        if line.startswith('full:'):
            domain = line[5:].strip()
            return domain
        
        # Handle plain domains (add dot prefix)
        if self.is_valid_domain(line):
            return f".{line}"
        
        # Skip invalid lines
        return None
    
    def is_valid_domain(self, domain):
        """Basic domain validation"""
        if not domain:
            return False
        
        # Basic domain pattern check
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        
        return bool(domain_pattern.match(domain)) and len(domain) <= 253

def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python convert_domains.py <source_dir> <output_dir>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    converter = DomainConverter(source_dir, output_dir)
    converter.convert_all_files()
    
    print("Conversion completed!")

if __name__ == "__main__":
    main()


def main_with_config():
    import sys
    import json
    
    parser = argparse.ArgumentParser(description='Convert v2fly domain lists to Surge format')
    parser.add_argument('source_dir', help='Source directory containing v2fly domain lists')
    parser.add_argument('output_dir', help='Output directory for Surge domain sets')
    parser.add_argument('--config', help='Configuration file (JSON)')
    
    args = parser.parse_args()
    
    converter = DomainConverter(args.source_dir, args.output_dir)
    
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        files_to_convert = config.get('files_to_convert', [])
        output_prefix = config.get('output_prefix', '')
        
        for filename in files_to_convert:
            if output_prefix:
                # Convert to file with prefix
                source_file = converter.source_dir / filename
                output_file = converter.output_dir / f"{output_prefix}{filename}"
                # ... conversion logic
            else:
                converter.convert_file(filename)
    else:
        converter.convert_all_files()
