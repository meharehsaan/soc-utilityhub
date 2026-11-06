import { checked, connectForm, readSource, requestTool, value, selectedFile, requestUploadedTool } from "../common.js";

// Run the explicitly configured certificate operation without saving the input.
async function runTool(signal) {
  const options = {};
  const file = selectedFile();
  if (file) {
    if (document.getElementById("source").value !== "") {
      throw new Error("Use pasted text or a file, not both.");
    }
    return requestUploadedTool("certificate", file, options, signal);
  }
  return requestTool("certificate", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "-----BEGIN CERTIFICATE-----\nMIIBNzCB3qADAgECAgEBMAoGCCqGSM49BAMCMBcxFTATBgNVBAMMDGV4YW1wbGUu\ndGVzdDAeFw0yNjAxMDEwMDAwMDBaFw0yNzAxMDEwMDAwMDBaMBcxFTATBgNVBAMM\nDGV4YW1wbGUudGVzdDBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABINzR9HlEWB9\niFg8cfGLwLTwib4N4OOn+XnXL6zZMQMV/rj2iEN6l4qz9L7W1tqAJkEkNYbhoqwB\nrSM6D769XQKjGzAZMBcGA1UdEQQQMA6CDGV4YW1wbGUudGVzdDAKBggqhkjOPQQD\nAgNIADBFAiA7Wmlp2E9ARu0BW/7Ib5z484I6fIFjz1aBm7QF9oIcXAIhAIxC3+BQ\nypMM25Yd6lfgxVuiTFVwP9MZIPJi+pnkl004\n-----END CERTIFICATE-----\n";
}

connectForm(runTool, example);
