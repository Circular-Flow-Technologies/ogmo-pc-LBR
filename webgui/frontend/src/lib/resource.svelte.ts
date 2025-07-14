export let resource = <T>(fn: () => Promise<T>, initialValue?: T) => {
  const _rune = $state<{ value: T | undefined; loading: boolean }>({
    value: initialValue,
    loading: true,
  });

  $effect(() => {
    fn().then((data) => {
      _rune.loading = false;
      _rune.value = data;
    });
  });

  return _rune;
};
