import { useState, useEffect } from 'react';
import apiService from '../services/api';

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [resultStats, setResultStats] = useState(null);
  const [dailyYield, setDailyYield] = useState([]); // 新增：每日良率统计
  const [topFailList, setTopFailList] = useState([]); // 新增：TOP10不良测试项

  // 提取为独立函数，便于手动刷新
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // 并行获取仪表盘所需的所有数据
      const [statusResponse, resultStatsResponse, dailyYieldResponse, topFailResponse] = await Promise.all([
        apiService.getStatus(),
        apiService.getResultStatistics(),
        apiService.getDailyYield(),
        apiService.getTopFailMeasurements()
      ]);
      setStatusData(statusResponse);
      setResultStats(resultStatsResponse);
      setDailyYield(dailyYieldResponse);
      setTopFailList(Array.isArray(topFailResponse) ? topFailResponse : []);
      setError(null);
    } catch (err) {
      console.error('获取仪表盘数据出错:', err);
      setError('获取数据时出现错误。请检查API服务器是否运行正常。');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">错误!</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }

  // 统计通过和失败数
  let passCount = 0;
  let failCount = 0;
  if (resultStats) {
    for (const [key, value] of Object.entries(resultStats)) {
      if (key === 'Pass') {
        passCount += value;
      } else {
        failCount += value; // 所有非Pass都算失败
      }
    }
  }
  const totalTests = passCount + failCount;
  // 计算通过率
  const passRate = totalTests > 0 ? ((passCount / totalTests) * 100).toFixed(1) : '0';

  return (
    <div className="container mx-auto px-4 py-6">
      {/* <div className="flex items-center mb-6">
        <h1 className="text-2xl font-bold mr-4">测试报告系统仪表盘</h1>
        <button
          className="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700 text-base"
          type="button"
          onClick={fetchDashboardData}
        >
          刷新
        </button>
      </div> */}
      
      
      
      {resultStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">测试结果统计</h2>
            <div className="flex flex-col space-y-4">
              <div className="bg-green-50 p-4 rounded-md">
                <div className="text-gray-500 text-sm">通过率</div>
                <div className="text-2xl font-bold text-green-600">{passRate}%</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-green-50 p-4 rounded-md">
                  <div className="text-gray-500 text-sm">通过</div>
                  <div className="text-xl font-semibold text-green-600">{passCount}</div>
                </div>
                <div className="bg-red-50 p-4 rounded-md">
                  <div className="text-gray-500 text-sm">失败</div>
                  <div className="text-xl font-semibold text-red-600">{failCount}</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">最近10天测试良率</h2>
            {dailyYield && dailyYield.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-center border border-gray-200">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="px-2 py-1 border">日期</th>
                      <th className="px-2 py-1 border">总数</th>
                      <th className="px-2 py-1 border">通过</th>
                      <th className="px-2 py-1 border">不良</th>
                      <th className="px-2 py-1 border">良率(%)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...dailyYield]
  .sort((a, b) => b.date.localeCompare(a.date))
  .slice(0, 10)
  .map(stat => (
    <tr key={stat.date}>
      <td className="px-2 py-1 border">{stat.date}</td>
      <td className="px-2 py-1 border">{stat.total}</td>
      <td className="px-2 py-1 border text-green-600">{stat.pass}</td>
      <td className="px-2 py-1 border text-red-600">{stat.fail}</td>
      <td className="px-2 py-1 border text-blue-600">{stat.yield}</td>
    </tr>
  ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500">没有测试日期数据</p>
            )}
          </div>
        </div>
      )}
      
      {statusData && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">系统状态</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">状态</div>
              <div className="text-xl font-semibold">{statusData.status}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">版本</div>
              <div className="text-xl font-semibold">{statusData.version}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">数据库</div>
              <div className="text-xl font-semibold">{statusData.database}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">报告总数</div>
              <div className="text-xl font-semibold">{statusData.report_count}</div>
            </div>
          </div>
        </div>
      )}

      {/* TOP10不良测试项统计 */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">TOP10 不良测试项</h2>
        {topFailList && topFailList.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-center border border-gray-200">
              <thead>
                <tr className="bg-gray-100">
                  <th className="px-2 py-1 border">排名</th>
                  <th className="px-2 py-1 border">测试项名称</th>
                  <th className="px-2 py-1 border">不良次数</th>
                </tr>
              </thead>
              <tbody>
                {topFailList.map((item, idx) => (
                  <tr key={item.name}>
                    <td className="px-2 py-1 border">{idx + 1}</td>
                    <td className="px-2 py-1 border text-red-700 font-semibold">{item.name}</td>
                    <td className="px-2 py-1 border text-red-600">{item.fail_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">暂无不良统计数据</p>
        )}
      </div>


      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">快速操作</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <a href="/reports" className="bg-blue-50 hover:bg-blue-100 p-4 rounded-md text-center transition-colors">
            <div className="text-blue-500 text-lg font-semibold">查看报告</div>
          </a>
          <a href="/measurements" className="bg-blue-50 hover:bg-blue-100 p-4 rounded-md text-center transition-colors">
            <div className="text-blue-500 text-lg font-semibold">测量数据</div>
          </a>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
