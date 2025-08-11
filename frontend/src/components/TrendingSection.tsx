import { TrendingUp, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PlaybookCard } from "@/components/PlaybookCard";
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { Database } from '@/integrations/supabase/types';

function useTrendingPlaybooks() {
  return useQuery<Database['public']['Tables']['playbooks']['Row'][]>({
    queryKey: ['trending-playbooks'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('playbooks')
        .select('*')
        .order('stars_count', { ascending: false })
        .limit(6);
      if (error) throw error;
      return data || [];
    },
  });
}

function getTag(structure: unknown): string {
  if (
    structure &&
    typeof structure === 'object' &&
    'tags' in structure &&
    Array.isArray((structure as any).tags)
  ) {
    return (structure as any).tags[0] || 'General';
  }
  return 'General';
}

export function TrendingSection() {
  const { data: playbooks = [], isLoading, isError } = useTrendingPlaybooks();

  if (isLoading) return <div className="p-8 text-center">Loading trending playbooks...</div>;
  if (isError) return <div className="p-8 text-center text-red-500">Failed to load trending playbooks.</div>;

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-accent" />
            <div>
              <h2 className="text-3xl font-bold">Trending This Week</h2>
              <p className="text-muted-foreground">
                Most popular playbooks based on views, forks, and stars
              </p>
            </div>
          </div>

          <Button variant="outline" className="group">
            View All Trending
            <ArrowRight className="h-4 w-4 ml-2 transition-transform group-hover:translate-x-1" />
          </Button>
        </div>

        {/* Trending Cards - 2 Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {playbooks.map((playbook, index) => (
            <PlaybookCard
              key={playbook.id}
              title={playbook.title}
              description={playbook.description}
              author={playbook.author_id || 'Unknown'}
              forks={playbook.forks_count ?? 0}
              stars={playbook.stars_count ?? 0}
              tag={getTag(playbook.structure)}
              lastUpdated={playbook.updated_at || ''}
              className={`animate-fade-in [animation-delay:${index * 150}ms]`}
            />
          ))}
        </div>
      </div>
    </section>
  );
}