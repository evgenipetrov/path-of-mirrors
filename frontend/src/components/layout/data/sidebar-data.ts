import {
  LayoutDashboard,
  Monitor,
  Bell,
  Palette,
  Wrench,
  UserCog,
  StickyNote,
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
          title: 'Notes',
          url: '/notes',
          icon: StickyNote,
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
