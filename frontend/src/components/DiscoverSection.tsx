import { useState } from "react";
import { ChevronLeft, ChevronRight, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PlaybookCard } from "@/components/PlaybookCard";
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { Database } from '@/integrations/supabase/types';

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

export function DiscoverSection() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const visibleCards = 3;
  const { data: playbooks = [], isLoading, isError } = usePlaybooks();
  const maxIndex = Math.max(0, playbooks.length - visibleCards);

  const handlePrevious = () => {
    setCurrentIndex(Math.max(0, currentIndex - 1));
  };

  const handleNext = () => {
    setCurrentIndex(Math.min(maxIndex, currentIndex + 1));
  };

  const visiblePlaybooks = playbooks.slice(currentIndex, currentIndex + visibleCards);

  if (isLoading) return <div className="p-8 text-center">Loading playbooks...</div>;
  if (isError) return <div className="p-8 text-center text-red-500">Failed to load playbooks.</div>;

  return (
    <section className="py-16 bg-muted/20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold mb-2">Discover Business Playbooks</h2>
            <p className="text-muted-foreground">
              Battle-tested strategies from successful founders and operators
            </p>
          </div>
          
          {/* Navigation Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={handlePrevious}
              disabled={currentIndex === 0}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={handleNext}
              disabled={currentIndex >= maxIndex}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Playbook Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {visiblePlaybooks.map((playbook, index) => (
            <PlaybookCard
              key={playbook.id}
              title={playbook.title}
              description={playbook.description}
              author={playbook.author_id || 'Unknown'}
              forks={playbook.forks_count ?? 0}
              stars={playbook.stars_count ?? 0}
              tag={getTag(playbook.structure)}
              className={`animate-fade-in [animation-delay:${index * 100}ms]`}
            />
          ))}
        </div>

        {/* View All Button */}
        <div className="text-center">
          <Button variant="outline" size="lg" className="group">
            View All Playbooks
            <ArrowRight className="h-4 w-4 ml-2 transition-transform group-hover:translate-x-1" />
          </Button>
        </div>

        {/* Progress Indicator */}
        <div className="flex justify-center mt-6 gap-2">
          {Array.from({ length: Math.ceil(playbooks.length / visibleCards) }).map((_, index) => (
            <button
              key={index}
              className={`w-2 h-2 rounded-full transition-all duration-200 ${
                Math.floor(currentIndex / visibleCards) === index
                  ? "bg-primary w-8"
                  : "bg-muted-foreground/30"
              }`}
              onClick={() => setCurrentIndex(index * visibleCards)}
            />
          ))}
        </div>
      </div>
    </section>
  );
}