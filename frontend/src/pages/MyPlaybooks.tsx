import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Edit, Eye, GitFork, Star, History, BarChart2, Search, Plus, BookOpen, Tag, Globe, Lock } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { Navigation } from '@/components/Navigation';

interface Playbook {
  id: string;
  title: string;
  description: string;
  tags: string[];
  license: string;
  visibility: 'public' | 'private';
  blog: string;
  files: Array<{
    name: string;
    size: number;
    type: string;
  }>;
  author: string;
  created_at: string;
  stars: number;
  forks: number;
  views: number;
}

const MyPlaybooks: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<'all' | 'mine' | 'others'>('all');
  const [sort, setSort] = useState<'newest' | 'oldest' | 'stars' | 'forks' | 'views'>('newest');
  const [searchTerm, setSearchTerm] = useState('');
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Create dummy playbooks for demonstration
  useEffect(() => {
    const dummyPlaybooks: Playbook[] = [
      {
        id: 'playbook-1',
        title: 'B2B SaaS Growth Hacking Playbook',
        description: 'A comprehensive guide to scaling B2B SaaS companies from $0 to $10M ARR using proven growth hacking techniques.',
        tags: ['SaaS', 'Growth', 'Marketing', 'B2B'],
        license: 'MIT',
        visibility: 'public',
        blog: `# B2B SaaS Growth Hacking Playbook

## Introduction
This playbook covers the essential strategies and tactics for scaling B2B SaaS companies.

## Key Growth Channels
- Content Marketing
- Product-Led Growth
- Account-Based Marketing
- Referral Programs

## Implementation Framework
1. Identify your ICP
2. Build a scalable sales process
3. Implement product-led growth
4. Optimize for retention`,
        files: [
          { name: 'growth-framework.pdf', size: 2048576, type: 'application/pdf' },
          { name: 'sales-process.docx', size: 1048576, type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
        ],
        author: 'Sarah Johnson',
        created_at: '2024-01-15T10:30:00Z',
        stars: 45,
        forks: 12,
        views: 1200
      },
      {
        id: 'playbook-2',
        title: 'Product Launch Strategy Guide',
        description: 'Step-by-step process for launching successful products in competitive markets with limited resources.',
        tags: ['Product', 'Launch', 'Strategy', 'MVP'],
        license: 'CC-BY',
        visibility: 'public',
        blog: `# Product Launch Strategy Guide

## Pre-Launch Phase
- Market research and validation
- MVP development
- Beta testing with early adopters

## Launch Phase
- Soft launch to select users
- Gather feedback and iterate
- Prepare for full launch

## Post-Launch
- Monitor key metrics
- Optimize based on data
- Scale successful channels`,
        files: [
          { name: 'launch-checklist.pdf', size: 1536000, type: 'application/pdf' },
          { name: 'metrics-dashboard.xlsx', size: 512000, type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }
        ],
        author: 'Mike Chen',
        created_at: '2024-01-10T14:20:00Z',
        stars: 32,
        forks: 8,
        views: 890
      },
      {
        id: 'playbook-3',
        title: 'Content Marketing Mastery',
        description: 'Complete framework for building a content marketing engine that drives organic growth and brand awareness.',
        tags: ['Content', 'Marketing', 'SEO', 'Brand'],
        license: 'Apache-2.0',
        visibility: 'private',
        blog: `# Content Marketing Mastery

## Content Strategy
- Audience research and persona development
- Content calendar planning
- SEO optimization techniques

## Content Creation
- Blog post writing framework
- Video content production
- Social media content strategy

## Distribution and Promotion
- Email marketing automation
- Social media promotion
- Influencer collaboration`,
        files: [
          { name: 'content-calendar.xlsx', size: 768000, type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' },
          { name: 'seo-checklist.pdf', size: 1024000, type: 'application/pdf' }
        ],
        author: 'Lisa Park',
        created_at: '2024-01-05T09:15:00Z',
        stars: 28,
        forks: 15,
        views: 750
      },
      {
        id: 'playbook-4',
        title: 'Remote Team Management',
        description: 'Best practices for building and managing high-performing remote teams in the digital age.',
        tags: ['Remote', 'Management', 'Team', 'Leadership'],
        license: 'MIT',
        visibility: 'public',
        blog: `# Remote Team Management

## Building Remote Culture
- Communication protocols
- Team building activities
- Trust and accountability

## Tools and Processes
- Project management tools
- Communication platforms
- Performance tracking

## Leadership in Remote Settings
- Managing distributed teams
- Conflict resolution
- Career development`,
        files: [
          { name: 'remote-policy.pdf', size: 1280000, type: 'application/pdf' },
          { name: 'team-templates.docx', size: 896000, type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
        ],
        author: 'David Kim',
        created_at: '2024-01-01T16:45:00Z',
        stars: 56,
        forks: 22,
        views: 1450
      }
    ];

    // Load existing playbooks from localStorage and combine with dummy data
    const existingPlaybooks = JSON.parse(localStorage.getItem('demo_playbooks') || '[]');
    setPlaybooks([...dummyPlaybooks, ...existingPlaybooks]);
    setIsLoading(false);
  }, []);

  const filteredPlaybooks = playbooks.filter(playbook => {
    const matchesSearch = playbook.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         playbook.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         playbook.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    if (filter === 'mine' && user) {
      return matchesSearch && playbook.author === user.full_name;
    } else if (filter === 'others' && user) {
      return matchesSearch && playbook.author !== user.full_name;
    }
    
    return matchesSearch;
  });

  const sortedPlaybooks = [...filteredPlaybooks].sort((a, b) => {
    switch (sort) {
      case 'newest':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case 'oldest':
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case 'stars':
        return b.stars - a.stars;
      case 'forks':
        return b.forks - a.forks;
      case 'views':
        return b.views - a.views;
      default:
        return 0;
    }
  });

  const handleView = (playbookId: string) => {
    navigate(`/playbook/${playbookId}`);
  };

  const handleEdit = (playbookId: string) => {
    // Implement edit functionality
    console.log('Edit playbook:', playbookId);
  };

  if (isLoading) return <div className="container mx-auto p-4">Loading playbooks...</div>;

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-6">My Playbooks</h1>
        
        <div className="flex flex-col md:flex-row gap-4 mb-6 items-center">
          <Tabs value={filter} onValueChange={(value) => setFilter(value as 'all' | 'mine' | 'others')} className="flex-grow">
            <TabsList>
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="mine">Mine</TabsTrigger>
              <TabsTrigger value="others">Others</TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="flex items-center gap-2">
            <Input
              placeholder="Search playbooks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full md:w-auto"
            />
            <Button variant="outline" size="icon"><Search className="h-4 w-4" /></Button>
          </div>

          <Select value={sort} onValueChange={(value) => setSort(value as 'newest' | 'oldest' | 'stars' | 'forks' | 'views')}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest</SelectItem>
              <SelectItem value="oldest">Oldest</SelectItem>
              <SelectItem value="stars">Stars</SelectItem>
              <SelectItem value="forks">Forks</SelectItem>
              <SelectItem value="views">Views</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedPlaybooks.map((playbook) => (
            <Card key={playbook.id} className="flex flex-col hover:shadow-lg transition-shadow cursor-pointer" onClick={() => handleView(playbook.id)}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg line-clamp-2">{playbook.title}</CardTitle>
                    <CardDescription className="line-clamp-2 mt-2">{playbook.description}</CardDescription>
                  </div>
                  <Badge variant="outline" className="flex items-center gap-1 ml-2">
                    {playbook.visibility === 'public' ? <Globe className="h-3 w-3" /> : <Lock className="h-3 w-3" />}
                    {playbook.visibility}
                  </Badge>
                </div>
                
                <div className="flex flex-wrap gap-1 mt-3">
                  {playbook.tags.slice(0, 3).map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      <Tag className="h-3 w-3 mr-1" />
                      {tag}
                    </Badge>
                  ))}
                  {playbook.tags.length > 3 && (
                    <Badge variant="outline" className="text-xs">+{playbook.tags.length - 3}</Badge>
                  )}
                </div>
              </CardHeader>
              
              <CardContent className="flex-grow flex flex-col justify-between">
                <div className="text-sm text-muted-foreground mb-4">
                  <p>By {playbook.author}</p>
                  <p>Created {new Date(playbook.created_at).toLocaleDateString()}</p>
                  <p>{playbook.files.length} file{playbook.files.length !== 1 ? 's' : ''}</p>
                </div>
                
                <div className="flex items-center gap-4 text-sm mb-4">
                  <span className="flex items-center"><Star className="h-4 w-4 mr-1" /> {playbook.stars}</span>
                  <span className="flex items-center"><GitFork className="h-4 w-4 mr-1" /> {playbook.forks}</span>
                  <span className="flex items-center"><Eye className="h-4 w-4 mr-1" /> {playbook.views}</span>
                </div>
                
                <div className="flex gap-2 mt-auto">
                  <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleView(playbook.id); }}>
                    <Eye className="h-4 w-4 mr-2" /> View
                  </Button>
                  {playbook.author === user?.full_name && (
                    <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleEdit(playbook.id); }}>
                      <Edit className="h-4 w-4 mr-2" /> Edit
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
          
          {sortedPlaybooks.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center py-12">
              <BookOpen className="h-24 w-24 text-muted-foreground mb-6" />
              <h2 className="text-2xl font-bold mb-2">No Playbooks Yet</h2>
              <p className="text-muted-foreground mb-6 text-center max-w-md">
                It looks like you haven't created any playbooks. Start building your knowledge base now!
              </p>
              <Button size="lg" onClick={() => navigate('/create')}>
                <Plus className="h-5 w-5 mr-2" /> Create Your First Playbook
              </Button>
            </div>
          )}
        </div>

        <Separator className="my-8" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Edits</CardTitle>
              <CardDescription>Log of all actions you've done.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">No recent edits to display.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
              <CardDescription>Mini analytics for your playbooks.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold">{sortedPlaybooks.length}</p>
                  <p className="text-muted-foreground">Playbooks</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{sortedPlaybooks.reduce((sum, p) => sum + p.stars, 0)}</p>
                  <p className="text-muted-foreground">Stars</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{sortedPlaybooks.reduce((sum, p) => sum + p.forks, 0)}</p>
                  <p className="text-muted-foreground">Forks</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{sortedPlaybooks.reduce((sum, p) => sum + p.views, 0)}</p>
                  <p className="text-muted-foreground">Views</p>
                </div>
              </div>
              <Button className="w-full mt-6" onClick={() => navigate('/analytics')}>
                <BarChart2 className="h-4 w-4 mr-2" /> View Full Analytics
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default MyPlaybooks;
