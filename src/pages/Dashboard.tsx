import React from 'react';
import {
  Video,
  Clock,
  TrendingUp,
  BarChart3,
  Users,
  Activity,
} from 'lucide-react';
import {
  Card,
  CardTitle,
  CardContent,
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

const videoData = [
  { name: 'Jan', videos: 8 },
  { name: 'Feb', videos: 12 },
  { name: 'Mar', videos: 5 },
  { name: 'Apr', videos: 15 },
  { name: 'May', videos: 10 },
];

const adPerformanceData = [
  { name: 'Jan', conversions: 20 },
  { name: 'Feb', conversions: 45 },
  { name: 'Mar', conversions: 32 },
  { name: 'Apr', conversions: 55 },
  { name: 'May', conversions: 50 },
];

export const Dashboard = () => {
  return (
    <div className="max-w-6xl mx-auto px-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">
          Dashboard
        </h1>
        <Button className="bg-blue-600 text-white hover:bg-blue-700">
          New Project
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        {[
          {
            icon: <Video className="w-6 h-6 text-blue-600" />,
            title: 'Processed Videos',
            value: '12',
            bg: 'bg-blue-100',
          },
          {
            icon: <Clock className="w-6 h-6 text-green-600" />,
            title: 'Processing Time',
            value: '2.5h',
            bg: 'bg-green-100',
          },
          {
            icon: (
              <TrendingUp className="w-6 h-6 text-purple-600" />
            ),
            title: 'Generated Ads',
            value: '45',
            bg: 'bg-purple-100',
          },
        ].map((stat, idx) => (
          <Card key={idx}>
            <CardContent>
              <div className="flex items-center">
                <div
                  className={`w-12 h-12 ${stat.bg} rounded-full flex items-center justify-center mr-4`}
                >
                  {stat.icon}
                </div>
                <div>
                  <p className="text-sm text-gray-500">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold">
                    {stat.value}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Graphs and Analytics */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardTitle>Video Processing Trends</CardTitle>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={videoData}
                margin={{
                  top: 20,
                  right: 30,
                  left: 0,
                  bottom: 0,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="videos"
                  stroke="#1E90FF"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Ad Performance & Conversions</CardTitle>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={adPerformanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="conversions" fill="#FFD700" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Additional Metrics */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        {[
          {
            icon: (
              <BarChart3 className="w-6 h-6 text-yellow-600" />
            ),
            title: 'Average CTR',
            value: '8.9%',
            bg: 'bg-yellow-100',
          },
          {
            icon: <Users className="w-6 h-6 text-pink-600" />,
            title: 'Audience Engagement',
            value: '65%',
            bg: 'bg-pink-100',
          },
          {
            icon: (
              <Activity className="w-6 h-6 text-indigo-600" />
            ),
            title: 'Conversion Rate',
            value: '12.4%',
            bg: 'bg-indigo-100',
          },
        ].map((metric, idx) => (
          <Card key={idx}>
            <CardContent>
              <div className="flex items-center">
                <div
                  className={`w-12 h-12 ${metric.bg} rounded-full flex items-center justify-center mr-4`}
                >
                  {metric.icon}
                </div>
                <div>
                  <p className="text-sm text-gray-500">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold">
                    {metric.value}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Projects */}
      <Card>
        <CardTitle>Recent Projects</CardTitle>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                title: 'Product Demo Video',
                info: 'Processed 2 days ago • 3 shorts generated',
              },
              {
                title: 'Marketing Campaign',
                info: 'Processed 5 days ago • 5 shorts generated',
              },
            ].map((project, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <h3 className="font-semibold">{project.title}</h3>
                  <p className="text-sm text-gray-500">
                    {project.info}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-gray-300 text-gray-600 hover:bg-gray-100"
                >
                  View Results
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
