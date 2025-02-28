const fs = require('fs');
const path = require('path');

// Create directories if they don't exist
if (!fs.existsSync('public')) {
  fs.mkdirSync('public');
}
if (!fs.existsSync('src')) {
  fs.mkdirSync('src');
}
if (!fs.existsSync('src/components')) {
  fs.mkdirSync('src/components');
}
if (!fs.existsSync('src/components/tabs')) {
  fs.mkdirSync('src/components/tabs');
}

// Move files to their proper locations
// 1. Move index.html to public/
if (fs.existsSync('index.html') && !fs.existsSync('public/index.html')) {
  fs.copyFileSync('index.html', 'public/index.html');
  console.log('Moved index.html to public/');
}

// 2. Make sure these files are in src/
const filesToMove = [
  'App.jsx',
  'index.jsx',
  'style.css'
];

filesToMove.forEach(file => {
  if (fs.existsSync(file) && !fs.existsSync(`src/${file}`)) {
    fs.copyFileSync(file, `src/${file}`);
    console.log(`Moved ${file} to src/`);
  }
});

// 3. Make sure component files are in src/components/tabs/
const tabComponents = [
  'TealiumAnalysisTab.jsx',
  'ContentAnalysisTab.jsx',
  'ScreenshotsTab.jsx'
];

tabComponents.forEach(component => {
  if (fs.existsSync(`components/tabs/${component}`) && 
      !fs.existsSync(`src/components/tabs/${component}`)) {
    fs.copyFileSync(
      `components/tabs/${component}`, 
      `src/components/tabs/${component}`
    );
    console.log(`Moved ${component} to src/components/tabs/`);
  }
});

console.log('Project structure has been fixed. You can now run npm start.'); 