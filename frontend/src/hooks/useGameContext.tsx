import { createContext, useContext, useState, ReactNode } from 'react';

export type Game = 'poe1' | 'poe2';

interface GameContextType {
  game: Game;
  setGame: (game: Game) => void;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

export function GameProvider({ children }: { children: ReactNode }) {
  const [game, setGame] = useState<Game>('poe1');

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
