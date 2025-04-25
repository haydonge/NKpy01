import { useState, useEffect } from 'react';
import apiService from '../services/api';

/**
 * 获取最近日期的每日良率统计
 * 返回 { [date]: { pass, fail, total, yield } }
 */
export default function useDailyYield(recentDates) {
  const [dailyStats, setDailyStats] = useState({});

  useEffect(() => {
    if (!recentDates || recentDates.length === 0) {
      setDailyStats({});
      return;
    }
    let cancelled = false;
    async function fetchStats() {
      const stats = {};
      for (const date of recentDates) {
        try {
          // 只获取当天的报告（确保后端支持 ?date=YYYYMMDD 过滤）
          const reports = await apiService.getReports({ date });
          let pass = 0;
          let fail = 0;
          for (const r of reports) {
            if (r.result === 'Pass') pass++;
            else fail++;
          }
          const total = pass + fail;
          stats[date] = {
            pass,
            fail,
            total,
            yield: total > 0 ? ((pass / total) * 100).toFixed(1) : '0',
          };
        } catch (e) {
          stats[date] = { pass: 0, fail: 0, total: 0, yield: '0' };
        }
      }
      if (!cancelled) setDailyStats(stats);
    }
    fetchStats();
    return () => { cancelled = true; };
  }, [recentDates.join(',')]);

  return dailyStats;
}
