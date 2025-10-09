---
title: House of Husk
date: 2025-10-09 13:45:00 +0900
categories: [Pwnable, Exploitation]
tags: [glibc, heap, house-of-husk, pwn]
---

# House of Husk

House of Husk는 glibc 2.27때 처음 도입되었지만, 현대 glibc(약간 응용시 glibc 2.41까지도 유효하다)에서도 가능한 exploit기법이면서 최소 2개의 AAW로도 공격이 가능해 굉장히 유용한 기법이다.

## printf 분석

`glibc 2.35` 기준으로 `printf`의 정의는 다음과 같다.

```cpp
#  defineprintf(...) \
__printf_chk (__USE_FORTIFY_LEVEL - 1, __VA_ARGS__)
```

그리고 `__printf_chk`는 다음과 같고, 이런 방식으로 쭉 들어가보자

```cpp
#include "nldbl-compat.h"

int
attribute_hidden
__printf_chk (int flag, const char *fmt, ...)
{
  va_list arg;
  int done;

  va_start (arg, fmt);
  done = __nldbl___vfprintf_chk (stdout, flag, fmt, arg);
  va_end (arg);

  return done;
}
```

`_nldbl__vfprintf_chk`

```cpp
int
attribute_compat_text_section
__nldbl___vfprintf_chk (FILE *s, int flag, const char *fmt, va_list ap)
{
  unsigned int mode = PRINTF_LDBL_IS_DBL;
  if (flag > 0)
    mode |= PRINTF_FORTIFY;

  return __vfprintf_internal (s, fmt, ap, mode);
}
```

`__vfprintf_internal`

```cpp
/* Internal versions of v*printf that take an additional flags
   parameter.  */
extern int __vfprintf_internal (FILE *fp, const char *format, va_list ap,
				unsigned int mode_flags)
    attribute_hidden;
```

매크로 따라간 `__vfprintf_internal`

```cpp
#ifndef COMPILE_WPRINTF
# define vfprintf	__vfprintf_internal
```

결국 `vfprintf`에 들어가게 된다.

그리고 `vfprintf`에는 다음과 같은 부분이 있다.([line 1271](https://elixir.bootlin.com/glibc/glibc-2.35/source/stdio-common/vfprintf-internal.c#L1271))

```cpp
/* Use the slow path in case any printf handler is registered.  */
if (__glibc_unlikely (__printf_function_table != NULL
        || __printf_modifier_table != NULL
        || __printf_va_arg_table != NULL))
goto do_positional;
```

이 부분을 보면, `__printf_function_table`, `__printf_modifier_table`, `__printf_va_arg_table` 중 하나라도 존재한다면 `do_positional`로 이동한다. 이 중 `__printf_function_table`같은 경우 사용자가 임의로 등록할 수 있는 부분이란 점을 기억하자.

> 💡 **또다른 방법**
>
> 위 코드의 if문에서 걸리지 않는다면, glibc은 일반적인 루틴을 수행한다.
>
> ```c
> /* Process whole format string.  */
> do {
> STEP0_3_TABLE;
> STEP4_TABLE;
> [...]
> /* Get current character in format string.  */
> JUMP (*++f, step0_jumps);
> [...]
> ```
>
> 그리고 더 밑부분에, 다른 방식으로 `do_positional`로 이동 가능한 통로가 있다.
>
> ```c
> LABEL (form_unknown):
>   if (spec ==L_('\0'))
>     {
> /* The format string ended before the specifier is complete.  */
> 				__set_errno (EINVAL);
> 				done = -1;
>       goto all_done;
>     }
> 
> /* If we are in the fast loop force entering the complicated one.  */  
> 				goto do_positional;
> }
> ```
>
> glibc이 제공된 지정자를 식별 불가능할 시 사용자 정의 핸들러 등으로 해결을 시도하며 이 때 `do_positional`으로 접근하게 된다.
{: .prompt-info }

```javascript
do_positional:
  done = printf_positional (s, format, readonly_format, ap, &ap_save,
			    done, nspecs_done, lead_str_end, work_buffer,
			    save_errno, grouping, thousands_sep, mode_flags);
```

`do_positional`은 `printf_positional`을 호출한다.

## 공격 루트

이 House of Husk에는 공격 가능한 루트가 3개 정도 있다.

1. `__printf_arginfo_table`
2. `__printf_function_table`
3. `__printf_va_arg_table`

이렇게 세가지의 공격 가능한 함수가 있는데 `__printf_va_arg_table`쓰는 방법은 있다 정도만 찾았고 설명된 글을 찾지 못해서 제외했다.

### __printf_arginfo_table

`printf_positional`의 [line 1678](https://elixir.bootlin.com/glibc/glibc-2.35/source/stdio-common/vfprintf-internal.c#L1678)을 보면 다음과 같이 동작한다.

```c
      /* Parse the format specifier.  */
#ifdef COMPILE_WPRINTF
      nargs += __parse_one_specwc (f, nargs, &specs[nspecs], &max_ref_arg);
#else
      nargs += __parse_one_specmb (f, nargs, &specs[nspecs], &max_ref_arg);
#endif
```

일반적인 상황에서 wide character는 사용 안되므로 자연스럽게 `__parse_one_specmb()`를 호출한다.

`__parse_one_specmb` 구현을 보면, [line 307](https://elixir.bootlin.com/glibc/glibc-2.35/source/stdio-common/printf-parsemb.c#L307)에 다음과 같이 나와있다.

```c
/* Get the format specification.  */  spec->info.spec = (wchar_t) *format++;
  spec->size = -1;
  if (__builtin_expect (__printf_function_table == NULL, 1)
      || spec->info.spec >UCHAR_MAX      ||__printf_arginfo_table[spec->info.spec] == NULL
/* We don't try to get the types for all arguments if the format
	 uses more than one.  The normal case is covered though.  If
	 the call returns -1 we continue with the normal specifiers.  */      || (int) (spec->ndata_args = (*__printf_arginfo_table[spec->info.spec])
					   (&spec->info, 1, &spec->data_arg_type,
					    &spec->size)) < 0)
```

여기서, format character의 인자 개수 확인을 위해서 `__printf_arginfo_table[spec->info.spec]` 에 있는 코드를 실행한다. `spec->info.spec`은 "파싱을 위한 문자\*0x8 을 담고 있다.

이 내용을 가지고 exploit을 시도한다면, 다음과 같은 과정을 거친다.

1. `__printf_function_table`을 readable한 주소로 설정한다  
   `do_positional` 접근 위해
2. `__printf_arginfo_table`에 fake chunk구성  
   예를 들어, `ord('d')` 대상이고 `win` 함수 실행하고 싶으면 `win-ord('d')*0x8`로 설정한다.

여기서 fake chunk 구성을 좀 더 자세히 말하면, 원래 `__printf_arginfo_table`이 동작할 때 %d에 접근한다면,

```c
// spec = 'd' (0x64)라고 가정
arginfo_func = *(__printf_arginfo_table + spec * 8)
             = *(__printf_arginfo_table + 0x64 * 8)
             = *(__printf_arginfo_table + 0x320)
```

이런 식으로 동작한다. 이 상황에서, `__printf_arginfo_table`을 `win-ord('d')*0x8`로 설정한다면 결국 `*(__printf_arginfo_table + spec * 8)`가 `*win` 이 될 것이기 때문이다.

만약 %d가 아니면 `ord('d')` 부분만 적당히 바꿔주면 된다.

### __printf_function_table

`printf_positional` [line 1875](https://elixir.bootlin.com/glibc/glibc-2.35/source/stdio-common/vfprintf-internal.c#L1875)부터 보면, 이런 부분이 있다.

```c
 /* Process format specifiers.  */
      while (1)
	{
	  extern printf_function **__printf_function_table;
	  int function_done;

	  if (spec <= UCHAR_MAX
	      && __printf_function_table != NULL
	      && __printf_function_table[(size_t) spec] != NULL)
	    {
	      const void **ptr = alloca (specs[nspecs_done].ndata_args
					 * sizeof (const void *));

	      /* Fill in an array of pointers to the argument values.  */
	      for (unsigned int i = 0; i < specs[nspecs_done].ndata_args;
		   ++i)
		ptr[i] = &args_value[specs[nspecs_done].data_arg + i];

	      /* Call the function.  */
	      function_done = __printf_function_table[(size_t) spec]
		(s, &specs[nspecs_done].info, ptr);
		[...]
```

코드를 간단히 설명하자면,

```c
extern printf_function **__printf_function_table;
```

`__printf_function_table`은 각 형식 지정자별로 어떤 함수를 실행해야 할 지 저장하는 포인터 배열이고 배열을 extern으로 가지고 온다.

```c
 if (spec <= UCHAR_MAX
	      && __printf_function_table != NULL
	      && __printf_function_table[(size_t) spec] != NULL)
```

이 부분에서는 각각, spec의 범위, 커스텀 핸들러 여부, 해당 형식 지정자에 대한 핸들러 여부를 확인하는데, 커스텀 핸들러를 따로 지정하지 않는 한 이 조건은 통과한다.

```c
const void **ptr = alloca (specs[nspecs_done].ndata_args * sizeof (const void *));
for (unsigned int i = 0; i < specs[nspecs_done].ndata_args; ++i)
    ptr[i] = &args_value[specs[nspecs_done].data_arg + i];
```

이 부분은 인수에 대한 포인터 배열을 만드는 부분인데, 사실 익스하는 입장에서 그리 중요하진 않다.

```c
function_done = __printf_function_table[(size_t) spec]
```

이 부분이 취약점이 터지는 부분이다. `__printf_arginfo_table` 을 생각하면 비슷한 점이 보이는데, `__printf_arginfo_table[spec->info.spec]`에서 `__printf_function_table[(size_t) spec]`로 바뀐 정도의 차이다.

> 💡 **참고**
>
> glibc 2.37 이상에서 Xprintf_buffer→printf_positional로 바뀌긴 했는데, 공격에 영향은 없다.
{: .prompt-info }

익스 방법도 진짜 차이가 거의 없다.

1. `__printf_function_table`을 readable한 주소로 설정한다
2. `__printf_arginfo_table`에 fake chunk구성  
   예를 들어, `ord('d')` 대상이고 `win` 함수 실행하고 싶으면 `win-ord('d')*0x8`로 설정한다.

여기서 1,2번의 `__printf_function_table`과 `__printf_arginfo_table`를 바꾸면 된다.

왜 순서가 반대냐 하면, `__printf_arginfo_table`이 `__printf_function_table`보다 먼저 사용되기 때문에 더미값이 아닌 값이 들어가있으면 crash발생 등으로 `__printf_function_table` 사용까지 도달하지 못 할 수 있기 때문이다.

## References

- https://4xura.com/binex/house-of-husk
- Dreamhack wheat-and-barley 공식풀이
