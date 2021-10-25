#SingleInstance Force
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%

Sleep, 4000
Loop 2000,
{
	Send, {space}
	MouseClick, left
	MouseMove, 250, 0, 0, R
	Sleep, 100
	MouseClick, left
	MouseMove, 250, 0, 0, R
	Sleep, 100
	MouseClick, left
	MouseMove, 0, 400, 0, R
	Sleep, 100
	MouseClick, left
	MouseMove, -400, 0, 0, R
	Sleep, 100
	MouseClick, left
	MouseMove, -100, -400, 0, R
	Sleep, 100
	Send, {space}
}

Esc::ExitApp
