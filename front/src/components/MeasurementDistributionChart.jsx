import React from 'react';
import ReactECharts from 'echarts-for-react';

/**
 * 测量数据分布图组件
 * @param {Object} props
 * @param {string} props.name 测试项名称
 * @param {number[]} props.values 测量值数组
 * @param {string} [props.unit] 单位
 */
// 支持 upperLimit/lowerLimit 参考线
export default function MeasurementDistributionChart({ name, values, unit, upperLimit, lowerLimit }) {
  if (!values || values.length === 0) return null;
  // 让分布更细腻：分桶数量更多
  const binCount = Math.max(30, Math.floor(values.length / 2), Math.ceil(Math.sqrt(values.length)));
  const finalBinCount = Math.min(binCount, 100); // 最多100个分桶，防止过细
  // 动态确定X轴范围，覆盖所有值和上下限
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (typeof lowerLimit === 'number') min = Math.min(min, lowerLimit);
  if (typeof upperLimit === 'number') max = Math.max(max, upperLimit);
  const binWidth = (max - min) / finalBinCount;
  // 计算每个bin的中心点用于value型x轴
  const binCenters = Array(finalBinCount).fill(0).map((_, i) => min + (i + 0.5) * binWidth);
  const bins = Array(finalBinCount).fill(0);
  values.forEach(v => {
    if (isNaN(v)) return;
    let idx = Math.floor((v - min) / binWidth);
    if (idx >= finalBinCount) idx = finalBinCount - 1;
    if (idx < 0) idx = 0;
    bins[idx]++;
  });

  // 构造 markLine（上限/下限竖线，X轴直接用数值）
  const markLines = [];
  if (typeof upperLimit === 'number') {
    markLines.push({
      xAxis: upperLimit,
      name: '上限',
      lineStyle: { color: '#f59e42', width: 2, type: 'dashed' },
      label: { formatter: '上限', color: '#f59e42', fontWeight: 'bold', position: 'insideTop' }
    });
  }
  if (typeof lowerLimit === 'number') {
    markLines.push({
      xAxis: lowerLimit,
      name: '下限',
      lineStyle: { color: '#42b7f5', width: 2, type: 'dashed' },
      label: { formatter: '下限', color: '#42b7f5', fontWeight: 'bold', position: 'insideTop' }
    });
  }

  const option = {
    title: {
      text: `${name} 分布图`,
      left: 'center',
      top: 10,
      textStyle: { fontSize: 16 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: params => {
        // params为数组，value型x轴
        const p = params[0];
        if (!p) return '';
        return `区间中心: ${p.value[0].toFixed(2)}<br/>数量: ${p.value[1]}`;
      }
    },
    xAxis: {
      type: 'value',
      min,
      max,
      name: unit || '',
      nameLocation: 'end',
      axisLabel: { rotate: 0 }
    },
    yAxis: {
      type: 'value',
      name: '频数',
    },
    series: [
      {
        type: 'bar',
        data: binCenters.map((x, i) => [x, bins[i]]),
        barWidth: (binWidth * 1.5),
        itemStyle: { color: '#3b82f6' },
        markLine: markLines.length > 0 ? { data: markLines } : undefined
      }
    ],
    grid: { left: 40, right: 20, bottom: 60, top: 50 }
  };

  return (
    <div style={{ width: '100%', height: 320, margin: '24px 0' }}>
      <ReactECharts option={option} style={{ height: '100%' }} />
    </div>
  );
}
