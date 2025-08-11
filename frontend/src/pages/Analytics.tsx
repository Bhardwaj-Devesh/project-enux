import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { BarChart2, Star, GitFork, Eye } from 'lucide-react';
import { Navigation } from '@/components/Navigation';

const Analytics: React.FC = () => {
  const { user } = useAuth();

  // For demo purposes, using dummy data
  const totalPlaybooks = 4;
  const totalStars = 161;
  const totalForks = 57;
  const totalViews = 4290;

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-6 flex items-center">
          <BarChart2 className="h-8 w-8 mr-2" /> Your Playbook Analytics
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Playbooks</CardTitle>
              <BarChart2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalPlaybooks}</div>
              <p className="text-xs text-muted-foreground">Your published playbooks</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Stars</CardTitle>
              <Star className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalStars}</div>
              <p className="text-xs text-muted-foreground">Across all your playbooks</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Forks</CardTitle>
              <GitFork className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalForks}</div>
              <p className="text-xs text-muted-foreground">Copies made of your playbooks</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Views</CardTitle>
              <Eye className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalViews}</div>
              <p className="text-xs text-muted-foreground">Combined views on your playbooks</p>
            </CardContent>
          </Card>
        </div>

        {/* You can add more detailed charts or tables here if needed */}
      </div>
    </div>
  );
};

export default Analytics;
