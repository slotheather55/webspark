@echo off
echo Cleaning up project...
rmdir /s /q node_modules
del package-lock.json

echo Installing dependencies...
npm install

echo Project has been fixed. Run npm start to start your application. 