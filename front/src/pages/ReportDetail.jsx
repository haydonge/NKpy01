import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiService from '../services/api';
// 新增：引入测量分布图组件
import MeasurementDistributionChart from '../components/MeasurementDistributionChart';

function ReportDetail() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportData, setReportData] = useState(null);

  useEffect(() => {
    const fetchReportDetail = async () => {
      try {
        setLoading(true);
        const data = await apiService.getReportDetail(id);
        setReportData(data);
        setError(null);
      } catch (err) {
        console.error(`获取报告详情出错 (ID: ${id}):`, err);
        setError('获取报告详情时出现错误');
      } finally {
        setLoading(false);
      }
    };

    fetchReportDetail();
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">错误!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
        <div className="mt-4">
          <Link to="/reports" className="text-blue-600 hover:underline">&larr; 返回报告列表</Link>
        </div>
      </div>
    );
  }

  const { report, test_info, measurements } = reportData || {};

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">测试报告详情</h1>
        <Link to="/reports" className="text-blue-600 hover:underline">&larr; 返回报告列表</Link>
      </div>
      
      {report && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">报告信息</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">报告 ID</div>
              <div className="text-lg font-medium">{report.id}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">序列号</div>
              <div className="text-lg font-medium">{report.serial_number}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">部件号</div>
              <div className="text-lg font-medium">{report.part_number}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">日期</div>
              <div className="text-lg font-medium">{report.date}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">时间</div>
              <div className="text-lg font-medium">{report.time}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">结果</div>
              <div className="text-lg font-medium">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${report.result === 'Pass' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {report.result === 'Pass' ? '通过' : '失败'}
                </span>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">文件名</div>
              <div className="text-lg font-medium">{report.filename}</div>
            </div>
          </div>
        </div>
      )}

      {/* 新增：数值型项目分布图 */}
      {measurements && measurements.length > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-700">数值型项目分布图</h2>
          {/* 仅对有足够数据的数值型项目绘制分布图 */}
          {(() => {
            // 按项目名称分组数值
            const numMap = {};
            measurements.forEach(m => {
              // 判断 result_value 是否为有效数值
              const val = Number(m.result_value);
              if (!isNaN(val)) {
                if (!numMap[m.name]) numMap[m.name] = { values: [], unit: m.unit_of_measure };
                numMap[m.name].values.push(val);
              }
            });
            // 仅渲染数据量大于1的项目
            return Object.entries(numMap).filter(([_, v]) => v.values.length > 1).map(([name, v]) => (
              <MeasurementDistributionChart key={name} name={name} values={v.values} unit={v.unit} />
            ));
          })()}
        </div>
      )}

      {test_info && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">测试信息</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">测试 ID</div>
              <div className="text-lg font-medium">{test_info.test_id}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">测试类型</div>
              <div className="text-lg font-medium">{test_info.test_type}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">测试软件</div>
              <div className="text-lg font-medium">{test_info.software_name}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">软件版本</div>
              <div className="text-lg font-medium">{test_info.software_version}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">操作员</div>
              <div className="text-lg font-medium">{test_info.operator}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-gray-500 text-sm">测试站</div>
              <div className="text-lg font-medium">{test_info.station_id}</div>
            </div>
          </div>
        </div>
      )}
      
      {measurements && measurements.length > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">测量数据</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    测试项
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    测量结果
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    范围
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {measurements.map(measurement => (
                  <tr key={measurement.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {measurement.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {measurement.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {measurement.result_value} {measurement.unit_of_measure}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${measurement.status === 'Pass' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {measurement.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {measurement.lower_limit !== null && measurement.upper_limit !== null ? (
                        `${measurement.lower_limit} - ${measurement.upper_limit} ${measurement.unit_of_measure}`
                      ) : (
                        'N/A'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReportDetail;
