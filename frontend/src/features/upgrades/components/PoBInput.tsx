/**
 * PoB Input Component
 *
 * Tabbed interface for uploading PoB XML files or pasting import codes.
 */

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Upload, Code } from 'lucide-react'
import type { Game } from '../types'

interface PoBInputProps {
  game: Game
  onParse: (input: { pobXml?: string; pobCode?: string }) => void
  isLoading?: boolean
}

export function PoBInput({ onParse, isLoading = false }: PoBInputProps) {
  const [activeTab, setActiveTab] = useState<'file' | 'code'>('code')
  const [pobCode, setPobCode] = useState('')
  const [file, setFile] = useState<File | null>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleFileUpload = async () => {
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      onParse({ pobXml: content })
    }
    reader.readAsText(file)
  }

  const handleCodeParse = () => {
    if (!pobCode.trim()) return
    onParse({ pobCode: pobCode.trim() })
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Import Path of Building</CardTitle>
        <CardDescription>
          Upload a .xml file or paste your PoB import code to analyze your build
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'file' | 'code')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="code">
              <Code className="mr-2 h-4 w-4" />
              Import Code
            </TabsTrigger>
            <TabsTrigger value="file">
              <Upload className="mr-2 h-4 w-4" />
              Upload File
            </TabsTrigger>
          </TabsList>

          <TabsContent value="code" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="pob-code">PoB Import Code</Label>
              <Textarea
                id="pob-code"
                placeholder="Paste your Path of Building import code here (long base64 string)..."
                value={pobCode}
                onChange={(e) => setPobCode(e.target.value)}
                rows={6}
                className="font-mono text-xs"
              />
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <p>
                  In Path of Building, go to Import/Export → Generate → Copy to get your code
                </p>
                {pobCode && (
                  <p className="font-mono">
                    {pobCode.length.toLocaleString()} chars
                    {pobCode.length < 5000 && (
                      <span className="text-amber-500 ml-2">
                        (typical codes are 10,000+ chars)
                      </span>
                    )}
                  </p>
                )}
              </div>
            </div>
            <Button
              onClick={handleCodeParse}
              disabled={!pobCode.trim() || isLoading}
              className="w-full"
            >
              {isLoading ? 'Parsing...' : 'Parse Build'}
            </Button>
          </TabsContent>

          <TabsContent value="file" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="pob-file">PoB XML File</Label>
              <Input
                id="pob-file"
                type="file"
                accept=".xml"
                onChange={handleFileChange}
              />
              {file && (
                <p className="text-sm text-muted-foreground">
                  Selected: {file.name}
                </p>
              )}
            </div>
            <Button
              onClick={handleFileUpload}
              disabled={!file || isLoading}
              className="w-full"
            >
              {isLoading ? 'Parsing...' : 'Upload and Parse'}
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
