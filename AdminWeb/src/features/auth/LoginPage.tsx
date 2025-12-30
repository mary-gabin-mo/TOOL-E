import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const LoginPage = () => {
  // Local state for form inputs
  const [ucid, setUcid] = useState('');
  const [password, setPassword] = useState('');

  const navigate = useNavigate();

  // Placeholder for API mutation hook
  // const loginMutation = useMutation({
  //   mutationFn: (data) => api.post('/login', data),
  //   onSuccess: () => {
  //     navigate('/dashboard');
  //   },
  //   onError: (error) => {
  //     // Handle error state
  //   }
  // });

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Functional logic placeholder
    // loginMutation.mutate({ ucid, password });
    console.log('Login clicked', { ucid, password });
    
    // Frontend-only redirect for now
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white text-black font-sans">
      {/* Header Section */}
      <div className="text-center mb-12">
        <h2 className="text-3xl font-normal mb-1">Schulich</h2>
        <h1 className="text-6xl font-bold tracking-tight mb-2">MAKERSPACE</h1>
        <h3 className="text-2xl font-light">Admin</h3>
      </div>

      {/* Login Form Card */}
      <div className="w-full max-w-md p-8 bg-white rounded-lg border border-gray-100 shadow-sm">
        <form onSubmit={handleLogin} className="space-y-6">
          
          {/* UCID / Email Input */}
          <div>
            <input
              type="text"
              placeholder="UCID / Email"
              value={ucid}
              onChange={(e) => setUcid(e.target.value)}
              className="w-full px-4 py-3 rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all bg-white text-gray-800 placeholder-gray-400"
            />
          </div>

          {/* Password Input */}
          <div>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all bg-white text-gray-800 placeholder-gray-400"
            />
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            className="w-full py-3 px-4 bg-[#242424] hover:bg-black text-white font-medium rounded-md transition-colors duration-200"
          >
            Sign In
          </button>

          {/* Error State Placeholder */}
          {/* {isError && (
            <div className="text-red-500 text-sm text-center mt-2">
              Invalid credentials. Please try again.
            </div>
          )} */}
          
          {/* Loading State Placeholder */}
          {/* {isLoading && (
             <div className="text-center">Loading...</div>
          )} */}

        </form>
      </div>
    </div>
  );
};
