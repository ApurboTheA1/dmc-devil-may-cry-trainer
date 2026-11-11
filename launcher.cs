using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Windows.Forms;

namespace DmCTrainerLauncher
{
    internal static class Program
    {
        private static int GetFreePort()
        {
            var l = new TcpListener(IPAddress.Loopback, 0);
            l.Start();
            int port = ((IPEndPoint)l.LocalEndpoint).Port;
            l.Stop();
            return port;
        }

        private static bool IsPortListening(int port)
        {
            try
            {
                using (var client = new TcpClient())
                {
                    var ar = client.BeginConnect(IPAddress.Loopback, port, null, null);
                    bool ok = ar.AsyncWaitHandle.WaitOne(150);
                    if (ok && client.Connected)
                    {
                        client.EndConnect(ar);
                        return true;
                    }
                }
            }
            catch { }
            return false;
        }

        private static string FindPythonExecutable()
        {
            string pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
            foreach (string rawDir in pathEnv.Split(Path.PathSeparator))
            {
                string dir = rawDir.Trim().Trim('"');
                if (string.IsNullOrEmpty(dir)) continue;
                string pyw = Path.Combine(dir, "pythonw.exe");
                if (File.Exists(pyw)) return pyw;
                string py = Path.Combine(dir, "python.exe");
                if (File.Exists(py))
                {
                    string siblingPyw = Path.Combine(Path.GetDirectoryName(py) ?? "", "pythonw.exe");
                    return File.Exists(siblingPyw) ? siblingPyw : py;
                }
            }

            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string pyRoot = Path.Combine(localApp, "Programs", "Python");
            if (Directory.Exists(pyRoot))
            {
                foreach (string sub in Directory.GetDirectories(pyRoot, "Python*"))
                {
                    string pyw = Path.Combine(sub, "pythonw.exe");
                    if (File.Exists(pyw)) return pyw;
                    string py = Path.Combine(sub, "python.exe");
                    if (File.Exists(py)) return py;
                }
            }
            return null;
        }

        [STAThread]
        private static void Main()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string appPy = Path.Combine(baseDir, "app.py");
            if (!File.Exists(appPy))
            {
                MessageBox.Show(
                    "Could not find app.py next to DmC_Trainer.exe.",
                    "DmC Trainer Launcher",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return;
            }

            string pythonExe = FindPythonExecutable();
            if (string.IsNullOrEmpty(pythonExe))
            {
                MessageBox.Show(
                    "Python 3 (pythonw.exe / python.exe) was not found in PATH or LocalAppData.",
                    "DmC Trainer Launcher",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return;
            }

            int port = GetFreePort();
            var psi = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = string.Format("\"{0}\" --port {1}", appPy, port),
                WorkingDirectory = baseDir,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            Process proc;
            try
            {
                proc = Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Failed to start trainer backend:\n" + ex.Message,
                    "DmC Trainer Launcher",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return;
            }

            // Wait briefly for server socket or fast crash
            for (int i = 0; i < 40; i++)
            {
                if (proc.HasExited)
                {
                    if (proc.ExitCode != 0)
                    {
                        MessageBox.Show(
                            "Trainer backend exited unexpectedly (code " + proc.ExitCode + ").\nEnsure 'flask' and 'psutil' Python packages are installed.",
                            "DmC Trainer Launcher",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        );
                    }
                    return;
                }
                if (IsPortListening(port))
                {
                    return;
                }
                Thread.Sleep(150);
            }
        }
    }
}
