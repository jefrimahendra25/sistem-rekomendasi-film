Write-Host "Menginstall dependensi..."
pip install -r requirements.txt

Write-Host "Menjalankan aplikasi..."
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
python app.py
