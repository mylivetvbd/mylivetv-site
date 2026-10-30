// My Live TV — Windows v2.0
const { app, BrowserWindow, shell } = require('electron');

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
  // বাইরের লিংক (স্টুডিও ইত্যাদি) ডিফল্ট ব্রাউজারে খুলবে
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
  // রক্ষাকবচ: কোনো বাইরের ঠিকানায় অ্যাপের ভেতরে যাওয়া আটকাও — ব্রাউজারে পাঠাও
  win.webContents.on('will-navigate', (e, url) => {
    if (url.indexOf('http') === 0) { e.preventDefault(); shell.openExternal(url); }
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
