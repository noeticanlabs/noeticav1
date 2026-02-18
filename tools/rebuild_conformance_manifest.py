#!/usr/bin/env python3
"""
Rebuild conformance manifest with actual file hashes.

This tool computes SHA-256 hashes for all conformance files and updates
the manifest to reflect the actual file contents.
"""

import hashlib
import json
import os
import sys
from pathlib import Path


def compute_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of file."""
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def get_file_size(filepath: Path) -> int:
    """Get file size in bytes."""
    if not filepath.exists():
        return 0
    return filepath.stat().st_size


def rebuild_manifest(manifest_path: str = "conformance/conformance_manifest.json") -> int:
    """Rebuild conformance manifest with actual hashes.
    
    Args:
        manifest_path: Path to conformance manifest JSON
        
    Returns:
        Number of errors encountered
    """
    manifest_file = Path(manifest_path)
    
    if not manifest_file.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        return 1
    
    # Load manifest
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    errors = 0
    conformance_dir = manifest_file.parent
    
    print(f"Rebuilding manifest: {manifest_path}")
    print("-" * 60)
    
    for artifact in manifest.get("artifacts", []):
        filepath = conformance_dir / artifact["file"]
        
        # Compute actual hash
        actual_hash = compute_hash(filepath)
        actual_size = get_file_size(filepath)
        
        old_hash = artifact.get("hash", "")
        
        if actual_hash == "FILE_NOT_FOUND":
            print(f"MISSING: {artifact['file']}")
            errors += 1
            continue
        
        # Update artifact
        artifact["hash"] = actual_hash
        artifact["size"] = actual_size
        
        # Check if hash changed
        if old_hash and old_hash != actual_hash:
            print(f"CHANGED: {artifact['file']}")
            print(f"  old: {old_hash[:16]}...")
            print(f"  new: {actual_hash[:16]}...")
        else:
            print(f"OK:     {artifact['file']}")
    
    # Save updated manifest
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("-" * 60)
    
    if errors > 0:
        print(f"WARNING: {errors} file(s) missing")
    else:
        print("Manifest rebuilt successfully")
    
    return errors


def main():
    """Main entry point."""
    manifest_path = sys.argv[1] if len(sys.argv) > 1 else "conformance/conformance_manifest.json"
    errors = rebuild_manifest(manifest_path)
    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
