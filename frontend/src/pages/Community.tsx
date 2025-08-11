import React from 'react';
import { Navigation } from '@/components/Navigation';

const Community: React.FC = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-4">Join Our Community</h1>
        <p className="text-lg mb-6">
          Connect with other founders, share your experiences, and learn from the best.
          Our community is a space for you to grow your network and get support on your entrepreneurial journey.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-2">Discord Server</h2>
            <p className="mb-4">Join our lively Discord community for real-time discussions, Q&A sessions, and virtual events.</p>
            <a href="#" className="text-blue-500 hover:underline">Join Now</a>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-2">Forum</h2>
            <p className="mb-4">Participate in in-depth discussions, ask for feedback, and share your own playbooks in our community forum.</p>
            <a href="#" className="text-blue-500 hover:underline">Visit the Forum</a>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-2">Events</h2>
            <p className="mb-4">Check out our upcoming webinars, workshops, and networking events.</p>
            <a href="#" className="text-blue-500 hover:underline">See Upcoming Events</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Community;
