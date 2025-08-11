import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, Search, Plus, Users } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

export default function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [selectedPath, setSelectedPath] = useState<string>("");

  const onboardingPaths = [
    {
      id: "create",
      title: "Create Your First Playbook",
      description: "Share your business knowledge and help other founders succeed",
      icon: Plus,
      action: () => navigate("/create"),
      color: "text-blue-500"
    },
    {
      id: "discover",
      title: "Discover Proven Playbooks",
      description: "Explore and fork successful business strategies from experienced founders",
      icon: Search,
      action: () => navigate("/search"),
      color: "text-green-500"
    },
    {
      id: "community",
      title: "Join the Community",
      description: "Connect with other founders and start collaborating on playbooks",
      icon: Users,
      action: () => navigate("/community"),
      color: "text-purple-500"
    }
  ];

  const handleGetStarted = () => {
    if (selectedPath) {
      const path = onboardingPaths.find(p => p.id === selectedPath);
      path?.action();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-muted/20 to-background">
      <Navigation />
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Welcome Header */}
          <div className="mb-12">
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
              <BookOpen className="h-4 w-4" />
              Welcome to Enux
            </div>
            
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Welcome{user?.full_name ? `, ${user.full_name}` : ''}!
            </h1>
            
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              You're now part of the world's first version-controlled knowledge network for startup best practices. 
              Let's get you started on your journey.
            </p>
          </div>

          {/* Onboarding Paths */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {onboardingPaths.map((path) => {
              const Icon = path.icon;
              return (
                <Card 
                  key={path.id}
                  className={`cursor-pointer transition-all duration-200 hover:scale-105 ${
                    selectedPath === path.id 
                      ? 'ring-2 ring-primary bg-primary/5' 
                      : 'hover:shadow-lg'
                  }`}
                  onClick={() => setSelectedPath(path.id)}
                >
                  <CardHeader className="text-center">
                    <div className="mx-auto mb-4 p-3 rounded-full bg-muted">
                      <Icon className={`h-6 w-6 ${path.color}`} />
                    </div>
                    <CardTitle className="text-lg">{path.title}</CardTitle>
                    <CardDescription>{path.description}</CardDescription>
                  </CardHeader>
                </Card>
              );
            })}
          </div>

          {/* Get Started Button */}
          <div className="space-y-4">
            <Button 
              size="lg" 
              className="px-8"
              disabled={!selectedPath}
              onClick={handleGetStarted}
            >
              Get Started
            </Button>
            
            <p className="text-sm text-muted-foreground">
              You can always change your focus later in your profile settings
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
