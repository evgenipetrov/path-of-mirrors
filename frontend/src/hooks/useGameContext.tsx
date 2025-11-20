/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, type ReactNode } from 'react';

export type Game = 'poe1' | 'poe2';

interface GameContextType {
  game: Game;
  setGame: (game: Game) => void;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

const STORAGE_KEY = 'pom-game-context';

export function GameProvider({ children }: { children: ReactNode }) {
  // Initialize from localStorage if available, otherwise default to 'poe1'
  const [game, setGameState] = useState<Game>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return (stored === 'poe1' || stored === 'poe2') ? stored : 'poe1';
  });

  // Persist to localStorage whenever game changes
  const setGame = (newGame: Game) => {
    setGameState(newGame);
    localStorage.setItem(STORAGE_KEY, newGame);
  };

  return (
    <GameContext.Provider value={{ game, setGame }}>
      {children}
    </GameContext.Provider>
  );
}

export function useGameContext() {
  const context = useContext(GameContext);
  if (context === undefined) {
    throw new Error('useGameContext must be used within a GameProvider');
  }
  return context;
}
