import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';

function Reports() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reports, setReports] = useState([]);
  const [filters, setFilters] = useState({
    serial_number: '',
    part_number: '',
    result: '',
    date_from: '', // 新增起始日期字段
    date_to: ''    // 新增结束日期字段
  });
  const [pagination, setPagination] = useState({
    limit: 10,
    offset: 0
  });

  const FAIL_TYPES = ['Fail', 'Aborted', 'Error', 'NG', 'Exceptional'];

  const fetchReports = async () => {
    try {
      setLoading(true);
      let data = [];
      if (filters.result === 'Fail') {
        // 并发请求所有“失败”类型
        const promises = FAIL_TYPES.map(type =>
          apiService.getReports({ ...pagination, ...filters, result: type })
        );
        const results = await Promise.all(promises);
        // 合并并去重（以id为唯一标识）
        const merged = [].concat(...results);
        const unique = [];
        const seen = new Set();
        for (const r of merged) {
          if (!seen.has(r.id)) {
            unique.push(r);
            seen.add(r.id);
          }
        }
        data = unique;
      } else {
        // 其它情况（如Pass或全部），只查一次
        data = await apiService.getReports({ ...pagination, ...filters });
      }
      setReports(data);
      setError(null);
    } catch (err) {
      console.error('获取测试报告列表出错:', err);
      setError('获取测试报告列表时出现错误');  
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    fetchReports();
  }, [pagination.offset, pagination.limit]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    // u91cdu7f6eu5206u9875u504fu79fbu91cfuff0cu4eceu7b2cu4e00u9875u5f00u59cb
    setPagination(prev => ({
      ...prev,
      offset: 0
    }));
    fetchReports();
  };

  const handleNextPage = () => {
    setPagination(prev => ({
      ...prev,
      offset: prev.offset + prev.limit
    }));
  };

  const handlePrevPage = () => {
    setPagination(prev => ({
      ...prev,
      offset: Math.max(0, prev.offset - prev.limit)
    }));
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">测试报告列表</h1>
      
      {/* 过滤器 */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <form onSubmit={handleSearch}>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
            <div>
              <label htmlFor="serial_number" className="block text-sm font-medium text-gray-700 mb-1">序列号</label>
              <input
                type="text"
                id="serial_number"
                name="serial_number"
                value={filters.serial_number}
                onChange={handleFilterChange}
                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="输入序列号"
              />
            </div>
            <div>
              <label htmlFor="part_number" className="block text-sm font-medium text-gray-700 mb-1">部件号</label>
              <input
                type="text"
                id="part_number"
                name="part_number"
                value={filters.part_number}
                onChange={handleFilterChange}
                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="输入部件号"
              />
            </div>
            <div>
              <label htmlFor="result" className="block text-sm font-medium text-gray-700 mb-1">测试结果</label>
              <select
                id="result"
                name="result"
                value={filters.result}
                onChange={handleFilterChange}
                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">所有结果</option>
                <option value="Pass">通过</option>
                <option value="Fail">失败</option>
              </select>
            </div>
            <div>
              <label htmlFor="date_from" className="block text-sm font-medium text-gray-700 mb-1">起始日期</label>
              <input
                type="date"
                id="date_from"
                name="date_from"
                value={filters.date_from}
                onChange={handleFilterChange}
                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="起始日期"
              />
            </div>
            <div>
              <label htmlFor="date_to" className="block text-sm font-medium text-gray-700 mb-1">结束日期</label>
              <input
                type="date"
                id="date_to"
                name="date_to"
                value={filters.date_to}
                onChange={handleFilterChange}
                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="结束日期"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
              搜索
            </button>
          </div>
        </form>
      </div>
      
      {/* 报告列表 */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500" />
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">错误!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      ) : (
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          {reports.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ID
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        序列号
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        部件号
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        日期
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        结果
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {(filters.result === 'Fail'
                      ? reports.filter(r => String(r.result).trim().toLowerCase() !== 'pass')
                      : filters.result === 'Pass'
                        ? reports.filter(r => String(r.result).trim().toLowerCase() === 'pass')
                        : reports
                    ).map(report => {
                      const isPass = String(report.result).trim().toLowerCase() === 'pass';
                      return (
                        <tr key={report.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{report.id}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{report.serial_number}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{report.part_number}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{report.date}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${isPass ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {isPass ? '通过' : '失败'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                            <Link to={`/reports/${report.id}`} className="hover:underline">查看详情</Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              {/* 分页控件 */}
              <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    type="button"
                    onClick={handlePrevPage}
                    disabled={pagination.offset === 0}
                    className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${pagination.offset === 0 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
                  >
                    上一页
                  </button>
                  <button
                    type="button"
                    onClick={handleNextPage}
                    disabled={reports.length < pagination.limit}
                    className={`ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${reports.length < pagination.limit ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
                  >
                    下一页
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      显示 <span className="font-medium">{reports.length}</span> 条结果
                      {pagination.offset > 0 && (
                        <span>, 从第 <span className="font-medium">{pagination.offset + 1}</span> 条开始</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <button
                        type="button"
                        onClick={handlePrevPage}
                        disabled={pagination.offset === 0}
                        className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 ${pagination.offset === 0 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
                      >
                        <span className="sr-only">上一页</span>
                        <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={handleNextPage}
                        disabled={reports.length < pagination.limit}
                        className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 ${reports.length < pagination.limit ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
                      >
                        <span className="sr-only">下一页</span>
                        <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="py-8 text-center text-gray-500">
              没有找到匹配的报告。请尝试修改搜索条件。
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Reports;
