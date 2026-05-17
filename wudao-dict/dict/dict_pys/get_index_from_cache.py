import os
import sys
import json

mp = []
input_file = sys.argv[1]
cache_dir = '../dcache/'
bad_cache_dir = '../bad_cache/'
output_file = 'c.txt'

lis = []
try:
    # Use with statement for automatic file closing
    with open(input_file, 'r') as f:
        lis = [x.strip() for x in f.readlines()]
except FileNotFoundError:
    print(f"Error: Input file not found at {input_file}")
    sys.exit(1)
except Exception as e:
    print(f"Error reading input file {input_file}: {e}")
    sys.exit(1)

### Add files from dcache ###
try:
    for fname in os.listdir(cache_dir):
        # Use os.path.join for cross-platform compatibility
        # Check if it's a file (optional, depends on expected content)
        # if os.path.isfile(os.path.join(cache_dir, fname)):
        lis.append(fname)
except FileNotFoundError:
    print(f"Error: Cache directory not found at {cache_dir}")
    # Decide if this is fatal or just a warning
except Exception as e:
    print(f"Error listing cache directory {cache_dir}: {e}")

### Process list ###
for v in lis:
    dcache_path = os.path.join(cache_dir, v)
    bad_cache_path = os.path.join(bad_cache_dir, v)

    if not os.path.exists(dcache_path):
        if not os.path.exists(bad_cache_path):
            # Print missing files relative to script location might be confusing.
            # Consider printing the full path or relative to a known base.
            print(f"Warning: Cache file not found in dcache or bad_cache: {v}")
        continue
    
    try:
        # Use with statement here too
        with open(dcache_path, 'r') as f:
            a = json.load(f)
        mp.append(a)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {dcache_path}: {e}")
    except FileNotFoundError: # Should be caught by os.path.exists, but good practice
         print(f"Error: File disappeared unexpectedly: {dcache_path}")
    except Exception as e: # Catch other potential errors like permission issues
        print(f"Error processing file {dcache_path}: {e}")

### Write output ###
try:
    # Use with statement for writing
    with open(output_file, 'w') as f:
        json.dump(mp, f, indent=4) # Add indent for readability
    print(f"Successfully wrote combined cache to {output_file}")
except IOError as e:
    print(f"Error writing output file {output_file}: {e}")
except Exception as e:
    print(f"An unexpected error occurred during writing: {e}")
