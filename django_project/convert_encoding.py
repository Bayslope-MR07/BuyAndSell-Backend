# convert_encoding.py

# Change 'temp.json' to your original dump filename if needed
input_file = 'temp.json'  
output_file = 'db_backup.json'

try:
    # Try reading with utf-16 (common cause of your error)
    with open(input_file, 'r', encoding='utf-16') as f_in:
        content = f_in.read()
except UnicodeError:
    # If utf-16 fails, try reading with 'latin-1' as a fallback (less strict)
    with open(input_file, 'r', encoding='latin-1') as f_in:
        content = f_in.read()

# Write the content back with utf-8 encoding
with open(output_file, 'w', encoding='utf-8') as f_out:
    f_out.write(content)

print(f"Converted '{input_file}' to UTF-8 and saved as '{output_file}'.")
