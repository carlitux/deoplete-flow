if exists('g:deoplete_flow_loaded')
  finish
endif

let g:deoplete_flow_loaded = 1

"Use locally installed flow from https://github.com/flowtype/vim-flow/issues/24
let local_flow = finddir('node_modules', '.;') . '/.bin/flow'
if matchstr(local_flow, "^\/\\w") == ''
    let local_flow= getcwd() . "/" . local_flow
endif
if executable(local_flow)
  let g:deoplete#sources#flow#flowbin = local_flow
else
  let g:deoplete#sources#flow#flowbin = 'flow'
endif
