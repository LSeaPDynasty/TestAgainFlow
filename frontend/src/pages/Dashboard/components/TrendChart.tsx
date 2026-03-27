import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface TrendChartProps {
  data: Array<{
    date: string;
    pass: number;
    fail: number;
  }>;
}

export const TrendChart: React.FC<TrendChartProps> = ({ data }) => {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-3">
          <p className="text-sm font-medium text-gray-700 mb-2">{payload[0].payload.date}</p>
          <div className="space-y-1">
            <p className="text-sm">
              <span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-2"></span>
              通过: <span className="font-semibold text-green-600">{payload[0].value}</span>
            </p>
            <p className="text-sm">
              <span className="inline-block w-3 h-3 rounded-full bg-red-500 mr-2"></span>
              失败: <span className="font-semibold text-red-600">{payload[1].value}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorPass" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#52C41A" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#52C41A" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorFail" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#FF4D4F" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#FF4D4F" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
          />
          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            height={36}
            iconType="circle"
            formatter={(value) => (
              <span className="text-sm text-gray-600">{value === 'pass' ? '通过' : '失败'}</span>
            )}
          />
          <Area
            type="monotone"
            dataKey="pass"
            stroke="#52C41A"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPass)"
          />
          <Area
            type="monotone"
            dataKey="fail"
            stroke="#FF4D4F"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorFail)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
