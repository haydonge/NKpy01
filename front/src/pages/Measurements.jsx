import React, { useEffect, useState } from 'react';
import apiService from '../services/api';

// 一个极简的测量筛选页面，只用于根据项目名称筛选测量值
export default function Measurements() {
  const [projectNames, setProjectNames] = useState([]);
  const [selectedName, setSelectedName] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = React.useRef();
  const [measurements, setMeasurements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 部件号相关状态
  const [partNumbers, setPartNumbers] = useState([]);
  const [selectedPartNumber, setSelectedPartNumber] = useState('');

  // 获取测量项目名称和部件号，实现双向联动
  useEffect(() => {
    async function fetchNames() {
      try {
        setLoading(true);
        setError(null);
        // 只要任一筛选发生变化都带上参数
        const params = {};
        if (selectedPartNumber) params.part_number = selectedPartNumber;
        if (selectedName) params.name = selectedName;
        const res = await apiService.getMeasurementNames(params);

        // 项目名称下拉
        const namesArr = Array.isArray(res?.names)
          ? res.names.map(item => item.name)
          : [];
        setProjectNames(namesArr);

        // 部件号下拉
        const partArr = Array.isArray(res?.part_numbers) ? res.part_numbers : [];
        setPartNumbers(partArr);

        // 若当前已选内容不在新列表中则自动清空
        if (selectedPartNumber && !partArr.includes(selectedPartNumber)) {
          setSelectedPartNumber('');
        }
        if (selectedName && !namesArr.includes(selectedName)) {
          setSelectedName('');
          setInputValue('');
        }
      } catch (err) {
        console.error('获取数据错误:', err);
        setError('获取项目名称失败');
      } finally {
        setLoading(false);
      }
    }
    fetchNames();
    // eslint-disable-next-line
  }, [selectedPartNumber, selectedName]); // 双向依赖，任一变化都重新获取

  // 输入框模糊搜索建议（仅输入时弹出建议，下拉选择不弹出）
  useEffect(() => {
    if (!inputValue) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    if (!inputActiveRef.current) {
      // 只有输入框聚焦且输入时才弹出建议
      setShowSuggestions(false);
      return;
    }
    setShowSuggestions(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const params = { q: inputValue };
        if (selectedPartNumber) params.part_number = selectedPartNumber;
        const res = await apiService.getMeasurementNames(params);
        const namesArr = Array.isArray(res?.names)
          ? res.names.map(item => item.name)
          : [];
        setSuggestions(namesArr);
      } catch {
        setSuggestions([]);
      }
    }, 500);
    return () => clearTimeout(debounceRef.current);
  }, [inputValue, selectedPartNumber]);

  // 选中项目后获取测量数据
  useEffect(() => {
    if (!selectedName) {
      setMeasurements([]);
      return;
    }
    async function fetchMeasurements() {
      try {
        setLoading(true);
        setError(null);
        
        // 构建查询参数，包含项目名称和部件号（如果选择了）
        const params = { name: selectedName };
        if (selectedPartNumber) {
          params.part_number = selectedPartNumber;
        }
        
        const data = await apiService.getMeasurements(params);
        const arr = Array.isArray(data?.measurements) ? data.measurements : [];
        setMeasurements(arr);
      } catch (err) {
        console.error('获取测量数据错误:', err);
        setError('获取测量数据失败');
        setMeasurements([]);
      } finally {
        setLoading(false);
      }
    }
    fetchMeasurements();
  }, [selectedName, selectedPartNumber]); // 添加 selectedPartNumber 依赖

  // 输入框是否处于激活（聚焦）状态
  const inputActiveRef = React.useRef(false);

  // 输入框回车或选择建议时，设置选中的项目名称
  const handleInputSelect = (name) => {
    setSelectedName(name);
    setInputValue(name);
    setShowSuggestions(false);
    setSuggestions([]);
  };

  // 输入框变化（仅更新输入内容，不筛查）
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    // 不再 setSelectedName，只有选建议或下拉时才筛查
  };


  // 输入框聚焦与失焦
  const handleFocus = () => {
    inputActiveRef.current = true;
    if (inputValue) setShowSuggestions(true);
  };
  const handleBlur = () => {
    inputActiveRef.current = false;
    setTimeout(() => setShowSuggestions(false), 100);
    // 不再自动筛查，只关闭建议
  };

  // 下拉选择（select）不会影响输入建议弹出




  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-lg font-semibold mb-4">项目测量值筛选</h2>
      
      {/* 部件号选择器 */}
      <div className="mb-4">
        <label htmlFor="part-number-select" className="block mb-1">选择部件号：</label>
        <select
          id="part-number-select"
          className="border px-2 py-1 rounded w-full"
          value={selectedPartNumber}
          onChange={e => setSelectedPartNumber(e.target.value)}
        >
          <option value="">-- 所有部件号 --</option>
          {partNumbers.map(partNumber => (
            <option key={partNumber} value={partNumber}>{partNumber}</option>
          ))}
        </select>
        <div className="text-xs text-gray-400 mt-1">
          {selectedPartNumber ? `当前选择的部件号: ${selectedPartNumber}` : '选择部件号可以筛选特定产品的测量数据'}
        </div>
      </div>
      
      {/* 项目名称选择器 */}
      <div className="mb-4 relative">
        <label htmlFor="project-input" className="block mb-1">输入或选择项目名称：</label>
          <input
            id="project-input"
            className="border px-2 py-1 rounded w-full"
            type="text"
            autoComplete="off"
            value={inputValue}
            onChange={handleInputChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder="输入项目名称..."
          />
        {showSuggestions && suggestions.length > 0 && (
          <ul className="border bg-yellow-100 absolute z-10 w-full mt-1 max-h-40 overflow-y-auto rounded shadow">
            {suggestions.map(name => (
              <li
                key={name}
                className="px-2 py-1 cursor-pointer hover:bg-blue-100"
                onMouseDown={() => handleInputSelect(name)}
              >
                {name}
              </li>
            ))}
          </ul>
        )}
        <div className="text-xs text-gray-400 mt-1">也可下拉选择：</div>
        <select
          id="project-select"
          className="border px-2 py-1 rounded w-full mt-1"
          value={selectedName}
          onChange={e => handleInputSelect(e.target.value)}
        >
          <option value="">-- 请选择 --</option>
          {projectNames.map(name => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
      </div>
      {loading && <div className="text-blue-500">加载中...</div>}
      {error && <div className="text-red-500 mb-2">{error}</div>}
      {selectedName && measurements.length > 0 && (
        <table className="min-w-full border mt-4">
          <thead>
            <tr>
              <th className="border px-2 py-1">ID</th>
              <th className="border px-2 py-1">部件号</th>
              <th className="border px-2 py-1">序列号</th>
              <th className="border px-2 py-1">值</th>
              <th className="border px-2 py-1">单位</th>
              <th className="border px-2 py-1">上限</th>
              <th className="border px-2 py-1">下限</th>
              <th className="border px-2 py-1">日期</th>
              <th className="border px-2 py-1">状态</th>
            </tr>
          </thead>
          <tbody>
            {measurements.map(m => (
              <tr key={m.id}>
                <td className="border px-2 py-1">{m.id}</td>
                <td className="border px-2 py-1">{m.part_number || ''}</td>
                <td className="border px-2 py-1">{m.serial_number || ''}</td>
                <td className="border px-2 py-1">{m.result_value}</td>
                <td className="border px-2 py-1">{m.unit_of_measure}</td>
                <td className="border px-2 py-1">{m.upper_limit}</td>
                <td className="border px-2 py-1">{m.lower_limit}</td>
                <td className="border px-2 py-1">{m.date || ''}</td>
                <td className="border px-2 py-1">{m.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {selectedName && !loading && measurements.length === 0 && !error && (
        <div className="text-gray-500 mt-4">该项目暂无测量数据。</div>
      )}
    </div>
  );
}
