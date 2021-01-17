#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
Sleep, 4000
Loop 2000,
{
if keep_x_running = n  ; Another thread signaled us to stop
	return
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