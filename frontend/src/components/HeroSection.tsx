import { Button } from "@/components/ui/button";
import { ArrowRight, GitFork, Users, BookOpen } from "lucide-react";

interface HeroSectionProps {
  onStartBuilding?: () => void;
}

export function HeroSection({ onStartBuilding }: HeroSectionProps) {
  return (
    <section className="relative py-20 lg:py-32 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-hero opacity-10"></div>
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-8 animate-fade-in">
            <GitFork className="h-4 w-4" />
            Version-controlled business knowledge
          </div>

          {/* Main heading */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6 animate-fade-in">
            <span className="bg-gradient-hero bg-clip-text text-transparent">
              GitHub for 
            </span>
            <br />
            <span className="text-foreground">
              Business Playbooks
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed animate-fade-in">
            Share, fork, and remix proven business strategies. 
            <br className="hidden md:block" />
            Built by founders, for founders.
          </p>

          {/* Stats */}
          <div className="flex flex-wrap justify-center gap-8 mb-10 animate-fade-in">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">1,200+</div>
              <div className="text-sm text-muted-foreground">Playbooks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">850+</div>
              <div className="text-sm text-muted-foreground">Contributors</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">15k+</div>
              <div className="text-sm text-muted-foreground">Forks</div>
            </div>
          </div>

          {/* CTA Button */}
          <div className="animate-scale-in">
            <Button 
              variant="hero" 
              size="xl" 
              className="group"
              onClick={onStartBuilding}
            >
              Start Building
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </Button>
          </div>

          {/* Features preview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-4xl mx-auto">
            <div className="bg-card/50 backdrop-blur border rounded-lg p-6 text-center animate-fade-in">
              <GitFork className="h-8 w-8 text-primary mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Fork & Customize</h3>
              <p className="text-sm text-muted-foreground">
                Clone proven strategies and adapt them to your business
              </p>
            </div>
            <div className="bg-card/50 backdrop-blur border rounded-lg p-6 text-center animate-fade-in">
              <Users className="h-8 w-8 text-primary mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Collaborate</h3>
              <p className="text-sm text-muted-foreground">
                Work together with pull requests and version control
              </p>
            </div>
            <div className="bg-card/50 backdrop-blur border rounded-lg p-6 text-center animate-fade-in">
              <BookOpen className="h-8 w-8 text-primary mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Learn & Share</h3>
              <p className="text-sm text-muted-foreground">
                Access battle-tested playbooks from successful founders
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}