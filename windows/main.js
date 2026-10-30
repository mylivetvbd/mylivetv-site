// My Live TV — Windows v2.0
const { app, BrowserWindow, shell } = require('electron');
const { exec } = require('child_process');

app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#040812',
    autoHideMenuBar: true,
    title: 'My Live TV',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false
    }
  });
  win.loadFile('app.html');
  // বাইরের লিংক খোলা: স্টুডিও হলে Edge-এ (বাংলা কণ্ঠ Edge-এই আছে)
  const openOutside = (url) => {
    if (process.platform === 'win32' && url.indexOf('studio') >= 0) {
      exec('start msedge "' + url + '"', (err) => { if (err) shell.openExternal(url); });
    } else {
      shell.openExternal(url);
    }
  };
  win.webContents.setWindowOpenHandler(({ url }) => {
    openOutside(url);
    return { action: 'deny' };
  });
  // রক্ষাকবচ: কোনো বাইরের ঠিকানায় অ্যাপের ভেতরে যাওয়া আটকাও — ব্রাউজারে পাঠাও
  win.webContents.on('will-navigate', (e, url) => {
    if (url.indexOf('http') === 0) { e.preventDefault(); openOutside(url); }
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
