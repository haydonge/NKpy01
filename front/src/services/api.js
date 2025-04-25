import axios from 'axios';

// API基础URL
const API_BASE_URL =
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : 'http://192.168.1.125:5000';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  // 启用跨域请求
  withCredentials: false,
});

// API服务
const apiService = {
  // 获取API状态
  getStatus: async () => {
    try {
      const response = await apiClient.get('/api/status');
      return response.data;
    } catch (error) {
      console.error('获取API状态出错:', error);
      throw error;
    }
  },

  // 获取所有测试报告
  getReports: async (params = {}) => {
    try {
      const response = await apiClient.get('/api/reports', { params });
      return response.data;
    } catch (error) {
      console.error('获取测试报告出错:', error);
      throw error;
    }
  },

  // 获取单个报告详情
  getReportDetail: async (reportId) => {
    try {
      const response = await apiClient.get(`/api/reports/${reportId}`);
      return response.data;
    } catch (error) {
      console.error(`获取报告详情出错 (ID: ${reportId}):`, error);
      throw error;
    }
  },

  // 获取结果统计
  getResultStatistics: async () => {
    try {
      const response = await apiClient.get('/api/statistics/results');
      return response.data;
    } catch (error) {
      console.error('获取结果统计出错:', error);
      throw error;
    }
  },

  // 获取日期统计
  getDateStatistics: async () => {
    try {
      const response = await apiClient.get('/api/statistics/by-date');
      return response.data;
    } catch (error) {
      console.error('获取日期统计出错:', error);
      throw error;
    }
  },

  // 获取每日良率统计
  getDailyYield: async () => {
    try {
      const response = await apiClient.get('/api/statistics/daily-yield');
      return response.data;
    } catch (error) {
      console.error('获取每日良率统计出错:', error);
      throw error;
    }
  },

  // 获取TOP10不良测试项
  getTopFailMeasurements: async () => {
    try {
      const response = await apiClient.get('/api/statistics/top-fail-measurements');
      return response.data;
    } catch (error) {
      console.error('获取TOP不良测试项出错:', error);
      throw error;
    }
  },

  // 获取测量数据
  getMeasurements: async (params = {}) => {
    try {
      console.log('发送请求到API: /api/measurements', { params });
      const response = await apiClient.get('/api/measurements', { params });
      console.log('API响应状态:', response.status);
      console.log('API响应头:', response.headers);
      console.log('API响应数据:', response.data);
      return response.data;
    } catch (error) {
      console.error('获取测量数据出错:', error);
      console.error('错误详情:', {
        message: error.message,
        response: error.response ? {
          status: error.response.status,
          data: error.response.data,
          headers: error.response.headers
        } : 'No response',
        request: error.request ? 'Request sent but no response received' : 'No request'
      });
      throw error;
    }
  },

  // 获取测量数据统计
  getMeasurementStats: async (params = {}) => {
    try {
      const response = await apiClient.get('/api/measurements/stats', { params });
      return response.data;
    } catch (error) {
      console.error('获取测量数据统计出错:', error);
      throw error;
    }
  },

  // 获取所有测试项名称
  getMeasurementNames: async (q = '') => {
    try {
      const params = q ? { q } : undefined;
      console.log('发送请求到API: /api/measurements/names', params);
      const response = await apiClient.get('/api/measurements/names', { params });
      console.log('API响应状态:', response.status);
      console.log('API测试项名称响应数据:', response.data);
      return response.data;
    } catch (error) {
      console.error('获取测量项名称出错:', error);
      console.error('错误详情:', {
        message: error.message,
        response: error.response ? {
          status: error.response.status,
          data: error.response.data
        } : 'No response'
      });
      // 出错时返回空数组而不是抛出异常，以避免页面崩溃
      return [];
    }
  },
};

export default apiService;
