import sys
import io
from services.read_csv import save_csv_to_db_student_answers

print("="*70)
print("TEST IMPORT MENGGUNAKAN FUNGSI ASLI")
print("="*70)

# Simulate uploaded file
with open("data_jawaban_dummy.csv", "rb") as f:
    file_content = f.read()

# Create mock uploaded file object
class MockUploadedFile:
    def __init__(self, content, name):
        self.content = content
        self.name = name
        self._position = 0
    
    def read(self):
        return self.content
    
    def seek(self, position):
        self._position = position

mock_file = MockUploadedFile(file_content, "data_jawaban_dummy.csv")

print("\nMenjalankan fungsi save_csv_to_db_student_answers()...")
print("-"*70)

# Capture output
old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    result = save_csv_to_db_student_answers(mock_file)
    output = sys.stdout.getvalue()
finally:
    sys.stdout = old_stdout

print(output)
print("-"*70)
print(f"\nResult: {result}")
print("="*70)
