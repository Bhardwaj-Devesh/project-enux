import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { PlaybookCard } from "@/components/PlaybookCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search } from "lucide-react";
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { Database } from '@/integrations/supabase/types';

const quickFilters = [
  "All", "Marketing", "Fundraising", "Product Launch", "Business Strategy", "Sales"
];

function usePlaybooks() {
  return useQuery<Database['public']['Tables']['playbooks']['Row'][]>({
    queryKey: ['playbooks'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('playbooks')
        .select('*');
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

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const tag = searchParams.get('tag') || '';
  const [activeFilter, setActiveFilter] = useState(tag || "All");
  const { data: playbooks = [], isLoading, isError } = usePlaybooks();

  const filteredPlaybooks = playbooks.filter(playbook => {
    const tag = getTag(playbook.structure);
    const matchesQuery =
      !query ||
      playbook.title?.toLowerCase().includes(query.toLowerCase()) ||
      playbook.description?.toLowerCase().includes(query.toLowerCase()) ||
      tag.toLowerCase().includes(query.toLowerCase());
    const matchesTag =
      activeFilter === "All" || tag === activeFilter;
    return matchesQuery && matchesTag;
  });

  if (isLoading) return <div className="p-8 text-center">Loading playbooks...</div>;
  if (isError) return <div className="p-8 text-center text-red-500">Failed to load playbooks.</div>;

  return (
    <div className="min-h-screen bg-background">
      <Navigation showSearchInNav={true} />
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Results Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Search className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-2xl font-bold">
              {query ? `Search results for "${query}"` : `Browse ${activeFilter === "All" ? "All" : activeFilter} Playbooks`}
            </h1>
          </div>
          <p className="text-muted-foreground">
            Found {filteredPlaybooks.length} playbook{filteredPlaybooks.length !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2 mb-8">
          {quickFilters.map((filter) => (
            <Button
              key={filter}
              variant={activeFilter === filter ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveFilter(filter)}
              className="transition-all"
            >
              {filter}
            </Button>
          ))}
        </div>

        {/* Results Grid */}
        {filteredPlaybooks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPlaybooks.map((playbook) => {
              const tag = getTag(playbook.structure);
              return (
                <Link 
                  key={playbook.id} 
                  to={`/playbook/${playbook.id}`}
                  className="block transition-transform hover:scale-105"
                >
                  <PlaybookCard
                    title={playbook.title}
                    description={playbook.description}
                    author={playbook.author_id || 'Unknown'}
                    forks={playbook.forks_count ?? 0}
                    stars={playbook.stars_count ?? 0}
                    tag={tag}
                  />
                </Link>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-xl font-semibold mb-2">No playbooks found</h3>
            <p className="text-muted-foreground mb-6">
              Try adjusting your search terms or filters
            </p>
            <Button asChild>
              <Link to="/">Back to Home</Link>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}