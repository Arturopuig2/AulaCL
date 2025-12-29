import os

# 1. Create a dummy file with Latin-1 encoding (containing 'Á', 0xC1)
filename = "test_latin1.txt"
content = "Hola, esto es un test con tildes: Árbol, Camión."
# Encode as Latin-1
with open(filename, "wb") as f:
    f.write(content.encode("latin-1"))

print(f"Created '{filename}' with Latin-1 encoding.")

# 2. Run the Normalization Logic (Simulating the code added to reading.py)
print("Running normalization logic...")
try:
    with open(filename, "rb") as f:
        raw_bytes = f.read()
    
    try:
        content_str = raw_bytes.decode("utf-8")
        print("Read as UTF-8 (Unexpected for this test)")
    except UnicodeDecodeError:
        print("Caught expected UnicodeDecodeError. Falling back to Latin-1...")
        content_str = raw_bytes.decode("latin-1")
        
    # Rewrite as pure UTF-8
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content_str)
        print("Rewrote file as UTF-8.")
        
except Exception as e:
    print(f"Error: {e}")

# 3. Verify it determines as UTF-8 now
try:
    with open(filename, "r", encoding="utf-8") as f:
        new_content = f.read()
    print("Success! File read safely as UTF-8.")
    print(f"Content: {new_content}")
except Exception as e:
    print(f"Failed to read as UTF-8: {e}")

# Cleanup
if os.path.exists(filename):
    os.remove(filename)
