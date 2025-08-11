import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, Bell, User, GitFork, Star, BookOpen } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface NavigationProps {
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  showSearchInNav?: boolean;
  isScrolled?: boolean;
  onLoginClick?: () => void;
}

export function Navigation({ 
  searchValue = "", 
  onSearchChange, 
  showSearchInNav = false,
  isScrolled = false,
  onLoginClick
}: NavigationProps) {
  const { user, signOut } = useAuth();
  
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSearchChange?.(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(searchValue.trim())}`;
    }
  };

  return (
    <nav className={cn(
      "sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
      isScrolled && "shadow-md"
    )}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <BookOpen className="h-7 w-7 text-primary" />
              <span className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Enux
              </span>
            </div>
          </div>

          {/* Search Bar - Only visible when showSearchInNav is true */}
          {showSearchInNav && (
            <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md mx-8">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search business strategies..."
                  className="pl-10 bg-background"
                  value={searchValue}
                  onChange={handleSearch}
                />
              </div>
            </form>
          )}

          {/* Right side actions */}
          <div className="flex items-center space-x-2">
            {/* Add Button */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Plus className="h-5 w-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-48" align="end">
                {user ? (
                  <div className="space-y-2">
                    <Link to="/create" className="w-full text-left px-3 py-2 text-sm hover:bg-muted rounded-md block">
                      Create Playbook
                    </Link>
                    <button className="w-full text-left px-3 py-2 text-sm hover:bg-muted rounded-md">
                      Import Playbook
                    </button>
                    <button className="w-full text-left px-3 py-2 text-sm hover:bg-muted rounded-md">
                      Upload Files
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-sm text-muted-foreground mb-3">
                      Sign in to create content
                    </p>
                    <Button size="sm" onClick={onLoginClick}>Sign In</Button>
                  </div>
                )}
              </PopoverContent>
            </Popover>

            {/* Notifications */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Bell className="h-5 w-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80" align="end">
                {user ? (
                  <div className="space-y-4">
                    <h4 className="font-medium">Notifications</h4>
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">
                        No new notifications
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-sm text-muted-foreground mb-3">
                      Sign in to see your notifications
                    </p>
                    <Button size="sm" onClick={onLoginClick}>Sign In</Button>
                  </div>
                )}
              </PopoverContent>
            </Popover>

            {/* User Account */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon">
                  <User className="h-5 w-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-48" align="end">
                {user ? (
                  <div className="space-y-2">
                    <Link to="/my-playbooks" className="w-full text-left px-3 py-2 text-sm hover:bg-muted rounded-md block">
                      My Playbooks
                    </Link>
                    <button className="w-full text-left px-3 py-2 text-sm hover:bg-muted rounded-md">
                      Settings
                    </button>
                    <div className="border-t pt-2">
                      <button 
                        onClick={signOut}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-muted rounded-md text-red-600"
                      >
                        Sign Out
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-sm text-muted-foreground mb-3">
                      Join the community
                    </p>
                    <Button size="sm" className="w-full" onClick={onLoginClick}>Sign In</Button>
                  </div>
                )}
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </div>
    </nav>
  );
}