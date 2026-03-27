import React from 'react';
import { TrophyOutlined, CloseCircleOutlined } from '@ant-design/icons';

interface FailureItem {
  name: string;
  count: number;
}

interface FailureRankingProps {
  data: FailureItem[];
}

export const FailureRanking: React.FC<FailureRankingProps> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <CloseCircleOutlined className="text-4xl mb-2 text-green-500" />
        <p>太棒了！暂无失败记录</p>
      </div>
    );
  }

  const maxCount = Math.max(...data.map((d) => d.count));

  return (
    <div className="space-y-3">
      {data.map((item, index) => {
        const percentage = (item.count / maxCount) * 100;
        const medal =
          index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : null;

        return (
          <div key={item.name} className="failure-item">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-lg w-6 text-center">{medal || `#${index + 1}`}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{item.name}</p>
              </div>
              <div className="flex items-center gap-1 text-red-500 font-semibold">
                <CloseCircleOutlined />
                <span className="text-sm">{item.count}</span>
              </div>
            </div>
            <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden ml-9">
              <div
                className="absolute top-0 left-0 h-full bg-gradient-to-r from-red-400 to-red-500 rounded-full transition-all duration-500"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
