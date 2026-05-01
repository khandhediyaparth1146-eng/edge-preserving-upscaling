import React from 'react'
import { motion } from 'framer-motion'
import { Atom, User, LogOut } from 'lucide-react'

export default function Header({ user, onOpenAuth, onLogout }) {
  return (
    <header className="px-8 py-6 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto rounded-full bg-white/[0.03] border border-white/10 backdrop-blur-xl py-3 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center">
            <Atom className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-sm font-bold text-white tracking-tight italic">
            EDGE GEN
          </h1>
        </div>

        <div className="flex items-center gap-8">
          
          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-4 bg-white/5 pl-4 pr-1.5 py-1 rounded-full border border-white/10">
                <span className="text-xs font-bold text-white/80">{user.name}</span>
                <button 
                  onClick={onLogout}
                  className="p-2 bg-white/10 hover:bg-red-500/20 hover:text-red-400 rounded-full transition-all text-white/40"
                  title="Sign out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-6">
                <button 
                  onClick={onOpenAuth}
                  className="text-[11px] font-bold text-white/40 hover:text-white uppercase tracking-widest"
                >
                  Sign in
                </button>
                <button 
                  onClick={onOpenAuth}
                  className="bg-white text-black text-[10px] font-black py-2.5 px-7 rounded-full hover:bg-gray-200 transition-all uppercase"
                >
                  Sign up
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
