import {
  LayoutDashboard,
  Monitor,
  Bell,
  Palette,
  Wrench,
  UserCog,
  StickyNote,
  Sparkles,
  Coins,
  BookOpen,
  BarChart3,
  Compass,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'satnaing',
    email: 'satnaingdev@gmail.com',
    avatar: '/avatars/shadcn.jpg',
  },
  navGroups: [
    {
      title: 'General',
      items: [
        {
          title: 'Dashboard',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Focus Build',
          url: '/build',
          icon: Sparkles,
        },
        {
          title: 'Notes',
          url: '/notes',
          icon: StickyNote,
        },
      ],
    },
    {
      title: 'Explore',
      items: [
        {
          title: 'Meta',
          url: '/meta',
          icon: Compass,
        },
        {
          title: 'Economy',
          url: '/economy',
          icon: Coins,
        },
        {
          title: 'Catalog',
          url: '/catalog',
          icon: BookOpen,
        },
        {
          title: 'Analysis',
          url: '/analysis',
          icon: BarChart3,
        },
      ],
    },
    {
      title: 'Settings',
      items: [
        {
          title: 'Profile',
          url: '/settings',
          icon: UserCog,
        },
        {
          title: 'Account',
          url: '/settings/account',
          icon: Wrench,
        },
        {
          title: 'Appearance',
          url: '/settings/appearance',
          icon: Palette,
        },
        {
          title: 'Notifications',
          url: '/settings/notifications',
          icon: Bell,
        },
        {
          title: 'Display',
          url: '/settings/display',
          icon: Monitor,
        },
      ],
    },
  ],
}
