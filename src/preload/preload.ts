import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electron", {
  saveFile: (data: string, filename: string) => ipcRenderer.invoke("save-file", data, filename),
  openFile: () => ipcRenderer.invoke("open-file"),
});