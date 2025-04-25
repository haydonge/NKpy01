import React, { useState } from 'react';
import xmlToReportJson from './xmlToReportJson';

export default function XmlImport() {
  const [folderHandle, setFolderHandle] = useState(null);
  const [xmlFiles, setXmlFiles] = useState([]);
  const [status, setStatus] = useState('');
  // 新增：分组统计结果
  const [importResult, setImportResult] = useState({success: [], skipped: [], failed: []});

  // 选择文件夹并读取所有XML文件
  const handleSelectFolder = async () => {
    setStatus('');
    try {
      // 仅支持File System Access API的浏览器
      const dirHandle = await window.showDirectoryPicker();
      setFolderHandle(dirHandle);
      const files = [];
      for await (const entry of dirHandle.values()) {
        if (entry.kind === 'file' && entry.name.endsWith('.xml')) {
          files.push(entry);
        }
      }
      setXmlFiles(files);
      setStatus(`找到 ${files.length} 个XML文件。`);
    } catch (e) {
      setStatus('未选择文件夹或浏览器不支持该功能。');
    }
  };

  // 提取通用的解析并上传XML函数
  async function parseAndUploadXmlFile(file, setStatus) {
    try {
      // 读取XML文件内容
      const text = await file.text();
      // 解析XML为DOM
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(text, "text/xml");
      // 检查解析错误
      const parseError = xmlDoc.getElementsByTagName('parsererror');
      if (parseError.length > 0) {
        setStatus(`XML解析错误: ${parseError[0].textContent}`);
        return { success: false, msg: `解析错误: ${file.name}` };
      }
      // 转为JSON
      const jsonData = xmlToReportJson(xmlDoc, file.name);
      // 上传JSON到后端
      setStatus(`正在上传 ${file.name}...`);
      const res = await fetch('http://localhost:5000/api/upload-xml-json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jsonData)
      });
      if (res.ok) {
        const result = await res.json();
        setStatus(`上传成功: ${file.name} ${result.message || ''}`);
        return { success: true, msg: result.message || '' };
      } else {
        const error = await res.json();
        setStatus(`上传失败: ${file.name} ${error.message || ''}`);
        return { success: false, msg: error.message || '' };
      }
    } catch (err) {
      setStatus(`错误: ${file.name} ${err.message}`);
      return { success: false, msg: err.message };
    }
  }

  // 批量上传所有XML文件到后端，循环调用通用函数
  const handleImport = async () => {
    if (!xmlFiles.length) {
      setStatus('没有可导入的XML文件。');
      return;
    }
    setStatus('开始处理...');
    let count = 0;
    let fail = 0;
    const success = [];
    const skipped = [];
    const failed = [];
    for (const fileHandle of xmlFiles) {
      try {
        const file = await fileHandle.getFile();
        const result = await parseAndUploadXmlFile(file, setStatus);
        if (result.success) {
          count++;
          success.push({ name: file.name, msg: result.msg });
        } else if (result.msg && result.msg.includes('同名文件已存在')) {
          skipped.push({ name: file.name, msg: result.msg });
        } else {
          fail++;
          failed.push({ name: file.name, msg: result.msg });
        }
        setStatus(`已处理 ${count + skipped.length + failed.length}/${xmlFiles.length}，成功 ${count}，重复 ${skipped.length}，失败 ${failed.length}`);
      } catch (e) {
        fail++;
        failed.push({ name: fileHandle.name, msg: e.message });
        setStatus(`处理 ${count + skipped.length + failed.length}/${xmlFiles.length}，失败 ${failed.length}: ${fileHandle.name} ${e.message}`);
      }
    }
    setStatus(`全部完成：成功 ${count}，重复 ${skipped.length}，失败 ${failed.length}`);
    setImportResult({ success, skipped, failed });
  };


  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-4">批量导入XML文件</h1>
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        type="button"
        onClick={handleSelectFolder}
      >
        选择XML文件夹
      </button>
      {xmlFiles.length > 0 && (
        <div className="my-4">
          <p>共找到 {xmlFiles.length} 个XML文件：</p>
          <ul className="list-disc ml-6">
            {xmlFiles.map(f => <li key={f.name}>{f.name}</li>)}
          </ul>
          <button
            className="mt-4 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            type="button"
            onClick={handleImport}
          >
            导入全部XML
          </button>
        </div>
      )}
      
      {/* 单文件上传和解析 */}
      <div className="my-4 p-4 border border-gray-300 rounded">
        <h2 className="text-lg font-semibold mb-2">单文件解析上传</h2>
        <input
          type="file"
          accept=".xml"
          className="mb-2"
          onChange={async (e) => {
            setStatus('');
            const file = e.target.files[0];
            if (!file) return;
            await parseAndUploadXmlFile(file, setStatus);
          }}
        />
        <p className="text-sm text-gray-500">选择单个XML文件，前端解析后上传到后端</p>
      </div>

      {status && <div className="mt-4 text-blue-700 whitespace-pre-line">{status}</div>}

      {/* 分组展示导入结果 */}
      {(importResult.success.length > 0 || importResult.skipped.length > 0 || importResult.failed.length > 0) && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">批量导入结果</h2>
          {importResult.success.length > 0 && (
            <div className="mb-2">
              <div className="font-bold text-green-700">成功导入 ({importResult.success.length})</div>
              <ul className="list-disc ml-6 text-green-700">
                {importResult.success.map(f => <li key={f.name}>{f.name} {f.msg && <span className="text-xs text-gray-500">({f.msg})</span>}</li>)}
              </ul>
            </div>
          )}
          {importResult.skipped.length > 0 && (
            <div className="mb-2">
              <div className="font-bold text-yellow-700">重复跳过 ({importResult.skipped.length})</div>
              <ul className="list-disc ml-6 text-yellow-700">
                {importResult.skipped.map(f => <li key={f.name}>{f.name} {f.msg && <span className="text-xs text-gray-500">({f.msg})</span>}</li>)}
              </ul>
            </div>
          )}
          {importResult.failed.length > 0 && (
            <div className="mb-2">
              <div className="font-bold text-red-700">导入失败 ({importResult.failed.length})</div>
              <ul className="list-disc ml-6 text-red-700">
                {importResult.failed.map(f => <li key={f.name}>{f.name} {f.msg && <span className="text-xs text-gray-500">({f.msg})</span>}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="mt-6 text-gray-500 text-sm">
        <p>说明：</p>
        <ul className="list-disc ml-6">
          <li>仅支持File System Access API的现代浏览器（如新版Chrome/Edge）。</li>
          <li>本页面支持批量上传XML文件到后端数据库。</li>
        </ul>
      </div>
    </div>
  );
}
