import { useState, useRef, useEffect } from "react";
import { Search, TrendingUp, DollarSign, Rocket, Target, Megaphone, Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SearchSectionProps {
  onSearch?: (query: string) => void;
  onSearchValueChange?: (value: string) => void;
  searchValue?: string;
  isVisible?: boolean;
}

const quickAccessButtons = [
  { label: "Trending", icon: TrendingUp, color: "text-orange-500" },
  { label: "Fundraising", icon: DollarSign, color: "text-green-500" },
  { label: "Product Launch", icon: Rocket, color: "text-blue-500" },
  { label: "Business Strategy", icon: Target, color: "text-purple-500" },
  { label: "Marketing", icon: Megaphone, color: "text-pink-500" },
  { label: "Sales", icon: Users, color: "text-indigo-500" },
];

export function SearchSection({ 
  onSearch, 
  onSearchValueChange, 
  searchValue = "", 
  isVisible = true 
}: SearchSectionProps) {
  const [localSearchValue, setLocalSearchValue] = useState(searchValue);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLocalSearchValue(searchValue);
  }, [searchValue]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (localSearchValue.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(localSearchValue.trim())}`;
    }
    onSearch?.(localSearchValue);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalSearchValue(value);
    onSearchValueChange?.(value);
  };

  const handleQuickAccess = (label: string) => {
    window.location.href = `/search?tag=${encodeURIComponent(label)}`;
  };

  if (!isVisible) return null;

  return (
    <section 
      ref={searchRef}
      className={cn(
        "py-16 bg-gradient-to-b from-muted/20 to-background transition-all duration-500",
        "animate-fade-in"
      )}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="mb-8">
            <div className="relative max-w-2xl mx-auto">
              <Search className="absolute left-6 top-1/2 h-6 w-6 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search business strategies, playbooks, and best practices..."
                className="pl-14 pr-6 h-16 text-lg rounded-2xl border-2 focus:border-primary bg-background shadow-lg"
                value={localSearchValue}
                onChange={handleInputChange}
              />
              <Button 
                type="submit"
                variant="default"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-12 px-6 rounded-xl"
              >
                Search
              </Button>
            </div>
          </form>

          {/* Quick Access Buttons */}
          <div className="flex flex-wrap justify-center gap-3">
            {quickAccessButtons.map((button) => {
              const Icon = button.icon;
              return (
                <Button
                  key={button.label}
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAccess(button.label)}
                  className="group hover:scale-105 transition-all duration-200"
                >
                  <Icon className={cn("h-4 w-4 mr-2", button.color)} />
                  {button.label}
                </Button>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}