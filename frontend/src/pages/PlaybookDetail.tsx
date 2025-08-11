import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Star, GitFork, Download, Share2, Eye, Calendar, User, ArrowLeft, Tag, Globe, Lock, FileText } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
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

export default function PlaybookDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isGuest } = useAuth();
  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load playbook from localStorage (demo data)
    const allPlaybooks = JSON.parse(localStorage.getItem('demo_playbooks') || '[]');
    const foundPlaybook = allPlaybooks.find((p: Playbook) => p.id === id);
    
    if (foundPlaybook) {
      setPlaybook(foundPlaybook);
    } else {
      // Check dummy data
      const dummyPlaybooks = [
        {
          id: 'playbook-1',
          title: 'B2B SaaS Growth Hacking Playbook',
          description: 'A comprehensive guide to scaling B2B SaaS companies from $0 to $10M ARR using proven growth hacking techniques.',
          tags: ['SaaS', 'Growth', 'Marketing', 'B2B'],
          license: 'MIT',
          visibility: 'public' as const,
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
          visibility: 'public' as const,
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
        }
      ];
      
      const dummyPlaybook = dummyPlaybooks.find(p => p.id === id);
      if (dummyPlaybook) {
        setPlaybook(dummyPlaybook);
      }
    }
    
    setIsLoading(false);
  }, [id]);

  const handleFork = () => {
    if (!user && !isGuest) {
      return;
    }
    if (isGuest) {
      alert("Please sign in to fork playbooks");
      return;
    }
    console.log("Forking playbook:", id);
  };

  const handleStar = () => {
    if (!user && !isGuest) {
      return;
    }
    if (isGuest) {
      alert("Please sign in to star playbooks");
      return;
    }
    console.log("Starring playbook:", id);
  };

  const renderMarkdownContent = (content: string) => {
    return content
      .split('\n')
      .map((line, index) => {
        if (line.startsWith('# ')) {
          return <h1 key={index} className="text-3xl font-bold mb-6 mt-8 first:mt-0">{line.substring(2)}</h1>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={index} className="text-2xl font-semibold mb-4 mt-6">{line.substring(3)}</h2>;
        }
        if (line.startsWith('### ')) {
          return <h3 key={index} className="text-xl font-medium mb-3 mt-4">{line.substring(4)}</h3>;
        }
        if (line.startsWith('- ')) {
          return <li key={index} className="ml-6 mb-2">{line.substring(2)}</li>;
        }
        if (line.startsWith('1. ')) {
          return <li key={index} className="ml-6 mb-2 list-decimal">{line.substring(3)}</li>;
        }
        if (line.trim() === '') {
          return <br key={index} />;
        }
        return <p key={index} className="mb-4 leading-relaxed">{line}</p>;
      });
  };

  if (isLoading) return <div className="p-8 text-center">Loading playbook...</div>;
  if (!playbook) return <div className="p-8 text-center text-red-500">Playbook not found.</div>;

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4 mb-4">
            <Button variant="ghost" onClick={() => navigate(-1)}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </div>
          
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">{playbook.title}</h1>
              <p className="text-muted-foreground mb-4">{playbook.description}</p>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span className="font-medium">{playbook.author}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span className="text-sm text-muted-foreground">
                    Created {new Date(playbook.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-4">
                {playbook.tags.map((tag, index) => (
                  <Badge key={index} variant="secondary" className="flex items-center gap-1">
                    <Tag className="h-3 w-3" />
                    {tag}
                  </Badge>
                ))}
                <Badge variant="outline" className="flex items-center gap-1">
                  {playbook.visibility === 'public' ? <Globe className="h-3 w-3" /> : <Lock className="h-3 w-3" />}
                  {playbook.visibility}
                </Badge>
                <Badge variant="outline">{playbook.license}</Badge>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <Button variant="outline" onClick={handleStar}>
                <Star className="w-4 h-4 mr-2" />
                Star ({playbook.stars})
              </Button>
              <Button variant="outline" onClick={handleFork}>
                <GitFork className="w-4 h-4 mr-2" />
                Fork ({playbook.forks})
              </Button>
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Download
              </Button>
              <Button variant="outline">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content - Blog */}
          <div className="lg:col-span-3">
            <Card>
              <CardContent className="p-8">
                <div className="prose max-w-none">
                  {renderMarkdownContent(playbook.blog)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Statistics */}
            <Card>
              <CardHeader>
                <CardTitle>Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Stars</span>
                  <span className="font-medium">{playbook.stars}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Forks</span>
                  <span className="font-medium">{playbook.forks}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Views</span>
                  <span className="font-medium">{playbook.views}</span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">License</span>
                  <Badge variant="outline">{playbook.license}</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Files */}
            <Card>
              <CardHeader>
                <CardTitle>Files & Assets</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {playbook.files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg border">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-blue-100 flex items-center justify-center">
                        <FileText className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <div className="font-medium text-sm">{file.name}</div>
                        <div className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</div>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4 mr-2" />
                      View
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Related Playbooks */}
            <Card>
              <CardHeader>
                <CardTitle>Related Playbooks</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { title: "Product Launch Checklist", author: "Mike Johnson" },
                  { title: "Sales Funnel Optimization", author: "Lisa Park" },
                  { title: "Content Marketing Guide", author: "David Kim" }
                ].map((related, index) => (
                  <div key={index} className="p-3 rounded-lg border hover:bg-accent cursor-pointer">
                    <div className="font-medium text-sm">{related.title}</div>
                    <div className="text-xs text-muted-foreground">by {related.author}</div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
