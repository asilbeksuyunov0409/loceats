#!/bin/bash

PROJECT_DIR="/home/loceats1/loyha3/loyha"
cd $PROJECT_DIR

echo "=== Settings fix ==="
sed -i "s/'HOST': 'mysql-8.4'/'HOST': 'localhost'/" $PROJECT_DIR/loceats/settings.py
sed -i "s/'USER': 'root'/'USER': 'loceats1_asilbek'/" $PROJECT_DIR/loceats/settings.py
sed -i "s/'NAME': 'loceats_db'/'NAME': 'loceats1_loceats_db'/" $PROJECT_DIR/loceats/settings.py
sed -i "s/'PASSWORD': ''/'PASSWORD': 'Asilbek@2005'/" $PROJECT_DIR/loceats/settings.py
grep -q 'GITHUB_WEBHOOK_SECRET' $PROJECT_DIR/loceats/settings.py || echo "GITHUB_WEBHOOK_SECRET = 'MySecretKey2024'" >> $PROJECT_DIR/loceats/settings.py

echo "=== Git pull ==="
git fetch origin main
git reset --hard origin/main

echo "=== Settings fix again ==="
sed -i "s/'HOST': 'mysql-8.4'/'HOST': 'localhost'/" $PROJECT_DIR/loceats/settings.py
sed -i "s/'USER': 'root'/'USER': 'loceats1_asilbek'/" $PROJECT_DIR/loceats/settings.py
sed -i "s/'NAME': 'loceats_db'/'NAME': 'loceats1_loceats_db'/" $PROJECT_DIR/loceats/settings.py
sed -i "s/'PASSWORD': ''/'PASSWORD': 'Asilbek@2005'/" $PROJECT_DIR/loceats/settings.py
grep -q 'GITHUB_WEBHOOK_SECRET' $PROJECT_DIR/loceats/settings.py || echo "GITHUB_WEBHOOK_SECRET = 'MySecretKey2024'" >> $PROJECT_DIR/loceats/settings.py

echo "=== Virtual env ==="
source /home/loceats1/virtualenv/loyha3/3.9/bin/activate

echo "=== Paketlar ==="
pip install -r requirements.txt --quiet

echo "=== Migrate ==="
python manage.py migrate --no-input

echo "=== Static ==="
python manage.py collectstatic --no-input

echo "=== Passenger restart ==="
mkdir -p $PROJECT_DIR/tmp
touch $PROJECT_DIR/tmp/restart.txt

echo "=== Deploy tugadi! ==="
