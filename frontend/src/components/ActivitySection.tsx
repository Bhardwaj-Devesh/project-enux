import { GitFork, Star, Upload, Eye, Award, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const recentActivities = [
  {
    id: 1,
    user: "Alex Chen",
    action: "forked",
    target: "Seed Fundraising Playbook 2024",
    time: "2 minutes ago",
    actionType: "fork" as const,
  },
  {
    id: 2,
    user: "Sarah Martinez",
    action: "starred",
    target: "Content Marketing Guide for MVP Launch",
    time: "5 minutes ago",
    actionType: "star" as const,
  },
  {
    id: 3,
    user: "David Kumar",
    action: "published",
    target: "Customer Discovery Framework",
    time: "12 minutes ago",
    actionType: "publish" as const,
  },
  {
    id: 4,
    user: "Emily Johnson",
    action: "forked",
    target: "B2B Sales Process Framework",
    time: "18 minutes ago",
    actionType: "fork" as const,
  },
  {
    id: 5,
    user: "Michael Wong",
    action: "starred",
    target: "Product-Market Fit Validation",
    time: "23 minutes ago",
    actionType: "star" as const,
  },
  {
    id: 6,
    user: "Lisa Thompson",
    action: "published",
    target: "Remote Team Onboarding Guide",
    time: "31 minutes ago",
    actionType: "publish" as const,
  },
  {
    id: 7,
    user: "Ryan Park",
    action: "forked",
    target: "Growth Hacking Strategies",
    time: "45 minutes ago",
    actionType: "fork" as const,
  },
  {
    id: 8,
    user: "Jennifer Lee",
    action: "starred",
    target: "Legal Startup Checklist",
    time: "1 hour ago",
    actionType: "star" as const,
  },
];

const topContributors = [
  {
    id: 1,
    name: "Sarah Chen",
    contributions: 23,
    reputation: 1847,
    specialty: "Marketing",
  },
  {
    id: 2,
    name: "Michael Rodriguez",
    contributions: 19,
    reputation: 1654,
    specialty: "Fundraising",
  },
  {
    id: 3,
    name: "David Park",
    contributions: 17,
    reputation: 1432,
    specialty: "Sales",
  },
  {
    id: 4,
    name: "Emily Johnson",
    contributions: 15,
    reputation: 1289,
    specialty: "Product",
  },
  {
    id: 5,
    name: "Alex Thompson",
    contributions: 13,
    reputation: 1156,
    specialty: "Operations",
  },
];

const getActionIcon = (actionType: string) => {
  switch (actionType) {
    case "fork":
      return <GitFork className="h-4 w-4 text-blue-500" />;
    case "star":
      return <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />;
    case "publish":
      return <Upload className="h-4 w-4 text-green-500" />;
    default:
      return <Eye className="h-4 w-4 text-gray-500" />;
  }
};

const getActionColor = (actionType: string) => {
  switch (actionType) {
    case "fork":
      return "text-blue-600";
    case "star":
      return "text-yellow-600";
    case "publish":
      return "text-green-600";
    default:
      return "text-gray-600";
  }
};

export function ActivitySection() {
  return (
    <section className="py-16 bg-muted/10">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Activity - 2/3 width */}
          <div className="lg:col-span-2">
            <div className="bg-card border rounded-xl p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Recent Activity
              </h3>
              
              <div className="space-y-4">
                {recentActivities.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors group"
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="text-xs bg-gradient-primary text-white">
                        {activity.user.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-sm">{activity.user}</span>
                        <span className={`text-sm ${getActionColor(activity.actionType)}`}>
                          {activity.action}
                        </span>
                        {getActionIcon(activity.actionType)}
                        <span className="text-sm text-foreground font-medium truncate">
                          {activity.target}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {activity.time}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Top Contributors - 1/3 width */}
          <div>
            <div className="bg-card border rounded-xl p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Award className="h-5 w-5 text-accent" />
                Top Contributors
              </h3>
              
              <div className="space-y-4">
                {topContributors.map((contributor, index) => (
                  <div
                    key={contributor.id}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors group"
                  >
                    <div className="flex-shrink-0">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                        index === 0 ? "bg-yellow-100 text-yellow-800" :
                        index === 1 ? "bg-gray-100 text-gray-800" :
                        index === 2 ? "bg-orange-100 text-orange-800" :
                        "bg-blue-100 text-blue-800"
                      }`}>
                        #{index + 1}
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">
                        {contributor.name}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          {contributor.specialty}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {contributor.contributions} contributions • {contributor.reputation} rep
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}