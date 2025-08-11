import { GitFork, Star, Eye, User, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface PlaybookCardProps {
  title: string;
  description: string;
  author: string;
  forks: number;
  stars: number;
  views?: number;
  tag: string;
  lastUpdated?: string;
  className?: string;
  variant?: "default" | "compact";
}

export function PlaybookCard({
  title,
  description,
  author,
  forks,
  stars,
  views,
  tag,
  lastUpdated,
  className,
  variant = "default"
}: PlaybookCardProps) {
  return (
    <div className={cn(
      "group bg-gradient-card border rounded-xl p-6 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer",
      "animate-fade-in",
      className
    )}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <Badge variant="secondary" className="text-xs">
          {tag}
        </Badge>
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
          <span>{stars}</span>
        </div>
      </div>

      {/* Title */}
      <h3 className="font-semibold text-lg mb-2 group-hover:text-primary transition-colors line-clamp-2">
        {title}
      </h3>

      {/* Description */}
      <p className="text-muted-foreground text-sm mb-4 line-clamp-2 leading-relaxed">
        {description}
      </p>

      {/* Author */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 bg-gradient-primary rounded-full flex items-center justify-center">
          <User className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-medium">{author}</span>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <GitFork className="h-4 w-4" />
            <span>{forks}</span>
          </div>
          {views && (
            <div className="flex items-center gap-1">
              <Eye className="h-4 w-4" />
              <span>{views}</span>
            </div>
          )}
          {lastUpdated && (
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>{lastUpdated}</span>
            </div>
          )}
        </div>
      </div>

      {/* Hover overlay */}
      <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl pointer-events-none" />
    </div>
  );
}

export function PlaybookCardSkeleton() {
  return (
    <div className="bg-card border rounded-xl p-6 animate-pulse">
      <div className="flex items-start justify-between mb-3">
        <div className="h-5 w-16 bg-muted rounded"></div>
        <div className="h-4 w-8 bg-muted rounded"></div>
      </div>
      <div className="h-6 w-3/4 bg-muted rounded mb-2"></div>
      <div className="h-4 w-full bg-muted rounded mb-1"></div>
      <div className="h-4 w-2/3 bg-muted rounded mb-4"></div>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 bg-muted rounded-full"></div>
        <div className="h-4 w-20 bg-muted rounded"></div>
      </div>
      <div className="flex items-center gap-4">
        <div className="h-4 w-12 bg-muted rounded"></div>
        <div className="h-4 w-12 bg-muted rounded"></div>
      </div>
    </div>
  );
}